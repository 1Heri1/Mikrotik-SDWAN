# Architecture

## Overview

```
┌─────────────┐      HTTPS       ┌──────────────────┐
│   Browser   │ ───────────────► │  nginx (frontend) │
└─────────────┘                  │  static SPA +     │
                                  │  reverse proxy    │
                                  └─────────┬─────────┘
                                            │ /api/*
                                            ▼
                                  ┌───────────────────┐
                                  │  FastAPI backend   │
                                  │  (gunicorn, 1 wkr) │
                                  │  ┌───────────────┐ │      binary API / REST
                                  │  │ APScheduler   │ │ ───────────────────────► Mikrotik
                                  │  │ (60s poll)    │ │                          concentrator
                                  │  └───────────────┘ │
                                  └─────────┬──────────┘
                                            │
                                            ▼
                                  ┌───────────────────┐
                                  │   PostgreSQL       │
                                  └───────────────────┘
```

The backend is a single FastAPI process. The APScheduler poll loop and the
HTTP API share the same event loop and the same database - there is no
separate worker service (no Celery/Redis), which is why the deployment is
pinned to a single gunicorn worker (see [Decisions](#decisions-log)).

## Backend layout

```
backend/app/
├── core/        # config, security (JWT/argon2), db session, crypto (Fernet),
│                  logging, in-memory rate limiter, auth dependencies
├── models/       # SQLAlchemy 2.0 ORM models (one file per table)
├── schemas/      # Pydantic request/response models
├── services/
│   ├── mikrotik/       # MikrotikBackend interface + librouteros/REST impls
│   ├── scheduler/      # APScheduler wrapper, poll/prune jobs, in-memory health state
│   ├── notifications/  # Telegram/SMTP channels + dispatcher
│   └── *_service.py    # business logic per resource (peers, alerts, audit, auth, router config)
├── api/routers/  # FastAPI routers - thin, delegate to services
├── cli.py        # admin user management (create-admin, reset-password, list-users)
└── main.py       # app wiring: lifespan (scheduler start/stop), CORS, exception handlers, routes
```

## Data flow: the poll cycle

Every `POLL_INTERVAL_SECONDS` (default 60), `services/scheduler/jobs.py:poll_job`:

1. Builds a `MikrotikBackend` from the active router configuration (DB row,
   falling back to `.env` bootstrap values before first setup).
2. Fetches active PPP connections, system resource, and the full secret list.
   Any connection/auth failure here raises a deduplicated `router_unreachable`
   critical alert and skips the rest of the cycle - it does **not** crash the
   scheduler.
3. Diffs active connections against configured `Peer` rows, inserts one
   `PeerStatusSnapshot` per peer, and updates each peer's denormalized
   `is_online` flag.
4. For peers offline longer than the configured threshold that were
   previously online, raises a `peer_offline` alert (deduplicated per peer).
   Recovery (back online, or router reachable again) auto-resolves the
   corresponding open alert and optionally sends a "recovered" notification.
5. A separate nightly job prunes `peer_status_snapshots` older than the
   configured retention window.

Alert notifications (Telegram/SMTP) are dispatched from `alert_service.py`
whenever a new alert is created or an existing one's re-notify cooldown has
elapsed - never on every single poll cycle while a condition persists.

## Data flow: a peer edit

1. Admin edits the form in `PeerDetailPage` and submits.
2. Frontend calls `POST /peers/{id}/preview` - `peer_service.preview_update`
   computes a pure before/after diff with **no side effects**.
3. `ConfirmDialog` + `DiffSummary` show the diff; the admin explicitly confirms.
4. Frontend calls `PATCH /peers/{id}` - `peer_service.update_peer` calls
   `MikrotikBackend.edit_secret(...)`, updates the local `Peer` row, and
   writes an `AuditLog` entry (password fields redacted to `***`).

The same preview-then-confirm shape is not required for enable/disable/reset
password (single, obviously-reversible actions with their own confirm
dialogs), but every mutating action is audit-logged regardless.

## Decisions log

- **Argon2 over bcrypt** for password hashing - current OWASP default, no
  72-byte input truncation footgun.
- **JWT access (15 min, in-memory on the frontend) + JWT refresh (httpOnly/
  Secure/SameSite=Strict cookie, path-scoped to `/api/auth/refresh`, rotated
  on every use, tracked in a `refresh_tokens` table)** rather than opaque
  server-side sessions - keeps the backend stateless for the access token
  while still allowing clean revocation of refresh tokens.
- **In-memory rate limiter and in-process APScheduler, no Redis/Celery** -
  appropriate at this app's scale (~200 peers, a handful of user accounts).
  The tradeoff is that both require the backend to run as a **single
  process** (`gunicorn --workers 1`); scaling to multiple workers would need
  a shared store (Redis) for both concerns first.
- **PPP secret passwords are Fernet-encrypted at rest, not stored in
  plaintext.** Mikrotik's API requires a plaintext password on `add`/`set`
  calls and never returns it on `print`, so the encrypted DB copy is the only
  source of truth for "what is this peer's current password" - used for
  in-app display (`reveal-password`, itself audit-logged) and for reset
  workflows. It is decrypted only transiently in memory.
- **`Peer.is_online` denormalized column** (in addition to full history in
  `peer_status_snapshots`) - avoids a correlated "latest snapshot per peer"
  subquery on every peers-list request for what is otherwise a hot, frequently
  polled 200-row table.
- **`refresh_tokens` and `notification_settings` tables** were added beyond
  the original data-model sketch: the former is required for secure refresh
  rotation, the latter so Telegram/SMTP config and alert thresholds are
  live-editable from the Settings page rather than requiring a restart.
- **TanStack Query over SWR** on the frontend - its mutation lifecycle
  (`onSuccess` cache invalidation) fits the preview-then-confirm peer edit
  flow naturally, and its `refetchInterval` covers the dashboard/peers-list
  auto-refresh needs without extra plumbing.
- **Dark theme by default** with a light-mode toggle (Tailwind `class`
  strategy, persisted to `localStorage`) - the toggle was low-cost to add
  alongside the required dark default.
- **Concentrator CPU/memory/uptime are kept in-memory only** (not persisted
  every poll) - the spec's historization requirement is about peer
  availability, not concentrator hardware metrics, so only "current health"
  is exposed on the dashboard; a restart simply clears it until the next
  successful poll.
- **Short-lived Mikrotik connections** (open, call, close) rather than a
  pooled/persistent connection - simpler error isolation for a 60s poller
  plus occasional admin actions, at a small per-call overhead cost that's
  irrelevant at this scale.
- **`librouteros` (binary API) is the default backend**, matching this
  concentrator's RouterOS < 7. A REST backend for RouterOS 7.x exists behind
  the same `MikrotikBackend` interface, selectable per-router via
  `router_config.protocol`, for when a future concentrator is upgraded.

## Known limitations

- Single-worker requirement (see above) - do not scale the backend
  horizontally or increase gunicorn workers without first moving the rate
  limiter and scheduler state to a shared store.
- No automated test coverage against a *real* Mikrotik router - this project
  was built without access to live hardware; `tests/test_mikrotik_client.py`
  mocks the `librouteros`/REST calls. Validate against your actual
  concentrator after deployment, starting with **Test connection** in
  Settings.

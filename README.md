# Mikrotik VPN Concentrator Monitor

A self-hosted web app for monitoring and partially managing a Mikrotik VPN
concentrator with ~200 PPTP/L2TP peer routers. It polls the concentrator
every 60 seconds, tracks peer availability history, raises alerts (Telegram /
email) on outages, and lets admins safely edit/disable/delete peers through a
confirm-before-apply workflow with a full audit trail.

See [ARCHITECTURE.md](ARCHITECTURE.md) for how it's built.

## Contents

- [Prerequisites](#prerequisites)
- [Option A: Docker Compose (recommended)](#option-a-docker-compose-recommended)
- [Option B: Docker-less (systemd + nginx)](#option-b-docker-less-systemd--nginx)
- [Creating the first admin user](#creating-the-first-admin-user)
- [Configuring the Mikrotik router](#configuring-the-mikrotik-router)
- [HTTPS](#https)
- [Notifications](#notifications)
- [Day-to-day operations](#day-to-day-operations)
- [Troubleshooting](#troubleshooting)

## Prerequisites

- Ubuntu 22.04 or 24.04 server
- A Mikrotik VPN concentrator reachable from this server, with PPP secrets
  already configured for your peer routers
- **Option A**: Docker Engine + the Docker Compose plugin
- **Option B**: Python 3.11+, Node.js 20+, PostgreSQL 14+, nginx

---

## Option A: Docker Compose (recommended)

1. Install Docker:

   ```bash
   curl -fsSL https://get.docker.com | sudo sh
   sudo usermod -aG docker $USER
   # log out/in for the group change to take effect
   ```

2. Get the code onto the server (e.g. `git clone` or `scp` this directory),
   then `cd` into it.

3. Create your environment file:

   ```bash
   cp .env.example .env
   ```

   Edit `.env` and set at minimum:
   - `POSTGRES_PASSWORD` (and make sure it matches inside `DATABASE_URL`)
   - `JWT_SECRET` - generate with:
     ```bash
     python3 -c "import secrets; print(secrets.token_urlsafe(64))"
     ```
   - `FERNET_KEY` - generate with:
     ```bash
     python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
     ```
     (If you don't have Python locally, run this inside the backend
     container after first build: `docker compose run --rm backend python -c "..."`.)
   - `CORS_ORIGINS` - the HTTPS origin(s) you'll access the app from
   - Optionally the `MIKROTIK_*` and `TELEGRAM_*` bootstrap values - you can
     also configure the router connection and notifications later from the
     Settings page instead.

4. Generate a self-signed certificate (replace with a real one later - see
   [HTTPS](#https)):

   ```bash
   mkdir -p certs
   openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
     -keyout certs/privkey.pem -out certs/fullchain.pem \
     -subj "/CN=mikrotik-monitor"
   ```

5. Build and start everything:

   ```bash
   docker compose up -d --build
   ```

   The backend container runs `alembic upgrade head` automatically on every
   start, so the database schema is always up to date.

6. Create the first admin user:

   ```bash
   docker compose exec backend python -m app.cli create-admin
   ```

7. Open `https://<server-ip-or-domain>/` and log in.

To update after pulling new code: `docker compose up -d --build`.

---

## Option B: Docker-less (systemd + nginx)

1. Install system packages:

   ```bash
   sudo apt update
   sudo apt install -y python3.11 python3.11-venv postgresql nginx nodejs npm
   ```

   (Use NodeSource or nvm if your distro's `nodejs` package is too old -
   Node 20+ is required to build the frontend.)

2. Create a dedicated system user and install directory:

   ```bash
   sudo useradd --system --create-home --shell /usr/sbin/nologin mikrotik-monitor
   sudo mkdir -p /opt/mikrotik-monitor
   sudo chown mikrotik-monitor:mikrotik-monitor /opt/mikrotik-monitor
   ```

   Copy this repository into `/opt/mikrotik-monitor` (e.g. `git clone` or
   `rsync`), owned by that user.

3. Create the PostgreSQL database:

   ```bash
   sudo -u postgres psql -c "CREATE USER mikrotik_monitor WITH PASSWORD 'change-me';"
   sudo -u postgres psql -c "CREATE DATABASE mikrotik_monitor OWNER mikrotik_monitor;"
   ```

4. Set up the backend:

   ```bash
   cd /opt/mikrotik-monitor/backend
   sudo -u mikrotik-monitor python3.11 -m venv .venv
   sudo -u mikrotik-monitor .venv/bin/pip install -r requirements.txt

   sudo cp ../deploy/systemd/mikrotik-monitor.env.example .env
   sudo chown mikrotik-monitor:mikrotik-monitor .env
   sudo -u mikrotik-monitor nano .env   # fill in real values, see comments in the file

   sudo -u mikrotik-monitor .venv/bin/alembic upgrade head
   sudo -u mikrotik-monitor .venv/bin/python -m app.cli create-admin
   ```

5. Install and start the systemd service:

   ```bash
   sudo cp ../deploy/systemd/mikrotik-monitor-backend.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable --now mikrotik-monitor-backend
   sudo systemctl status mikrotik-monitor-backend
   ```

6. Build the frontend and publish the static files:

   ```bash
   cd /opt/mikrotik-monitor/frontend
   npm ci
   npm run build
   sudo mkdir -p /var/www/mikrotik-monitor
   sudo cp -r dist/* /var/www/mikrotik-monitor/
   ```

7. Generate a certificate and install the nginx site:

   ```bash
   sudo mkdir -p /etc/nginx/certs
   sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
     -keyout /etc/nginx/certs/privkey.pem -out /etc/nginx/certs/fullchain.pem \
     -subj "/CN=mikrotik-monitor"

   sudo cp ../deploy/nginx/mikrotik-monitor.conf /etc/nginx/sites-available/
   sudo ln -s /etc/nginx/sites-available/mikrotik-monitor.conf /etc/nginx/sites-enabled/
   sudo rm -f /etc/nginx/sites-enabled/default
   sudo nginx -t && sudo systemctl reload nginx
   ```

8. Open `https://<server-ip-or-domain>/` and log in.

To update after pulling new code: reinstall backend deps if
`requirements.txt` changed, re-run `alembic upgrade head`, restart the
service, and rebuild/republish the frontend.

---

## Creating the first admin user

```bash
# Docker
docker compose exec backend python -m app.cli create-admin

# Docker-less
/opt/mikrotik-monitor/backend/.venv/bin/python -m app.cli create-admin
```

Additional CLI commands: `reset-password`, `list-users`. Run
`python -m app.cli --help` for details. Further users (including additional
admins or read-only `viewer` accounts) can also be created from the Settings
page once you're logged in.

## Configuring the Mikrotik router

Once logged in, go to **Settings → Router connection** and enter the
concentrator's host/port, API credentials, and protocol
(`librouteros` for RouterOS < 7, `rest` for RouterOS 7.x). Use **Test
connection** to verify before saving.

**Strongly recommended:** don't use your main admin account for this. Create
a dedicated, restricted API user on the Mikrotik first:

```
/user group add name=monitor-api-group policy=read,write,api,!local,!telnet,!ssh,!ftp,!reboot,!password,!sensitive,!romon
/user add name=monitor-api group=monitor-api-group password=<a-strong-password>
```

This user can read PPP secrets/active connections and add/edit/disable/remove
PPP secrets, but cannot reboot the router, change its own password policy, or
otherwise touch the rest of the configuration. The app never automates this
step for you - create it yourself, once, on the router.

## HTTPS

The app is not designed to run over plain HTTP outside local development.
Both deployment options start with a self-signed certificate so you can get
running immediately. Once you have a real domain pointed at the server:

- **Docker**: use `docker-compose.override.yml.example` as a starting point
  to add a `certbot` service and mount its output over `./certs`.
- **Docker-less**: install certbot (`sudo apt install certbot
  python3-certbot-nginx`) and run `sudo certbot --nginx`, which will edit the
  installed site config in place.

## Notifications

Configure Telegram (and optionally SMTP) from **Settings → Notifications &
alerts**, or via the `TELEGRAM_*` / `SMTP_*` variables in `.env` as bootstrap
defaults. To get a Telegram bot token, talk to
[@BotFather](https://t.me/BotFather); to find your chat ID, message your new
bot once and check `https://api.telegram.org/bot<TOKEN>/getUpdates`. Use the
**Send test message** button in Settings to confirm delivery.

## Day-to-day operations

- **Logs**: written to `LOG_DIR` (`/var/log/mikrotik-monitor` by default)
  with rotation (5 MB × 5 files), and also to stdout (`docker compose logs
  backend` / `journalctl -u mikrotik-monitor-backend`).
- **Database backups**: standard PostgreSQL practices apply - e.g.
  `docker compose exec postgres pg_dump -U <user> <db> > backup.sql`, or
  back up the `pg_data` volume / your system Postgres data directory.
- **Snapshot retention**: peer status history is pruned nightly based on
  "Snapshot retention (days)" in Settings (default 30).

## Troubleshooting

- **Login works but the dashboard shows "Unreachable"**: check the router
  connection in Settings, and confirm the concentrator allows API
  connections from this server's IP (firewall / `/ip service` on RouterOS).
- **No Telegram messages**: check the bot token/chat ID and use the test
  button; check backend logs for `Telegram notification failed`.
- **Migrations fail on startup (Docker)**: check `docker compose logs
  postgres` - usually a credentials/`DATABASE_URL` mismatch.

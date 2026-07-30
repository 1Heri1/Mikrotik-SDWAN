from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.logging import LOGGER_SCHEDULER, get_logger
from app.core.timeutils import ensure_aware
from app.models.peer import Peer
from app.models.peer_status_snapshot import PeerStatusSnapshot
from app.services import alert_service, router_config_service
from app.services.mikrotik.exceptions import MikrotikAuthError, MikrotikConnectionError, MikrotikError
from app.services.notifications.dispatcher import get_or_create_settings
from app.services.scheduler import state

logger = get_logger(LOGGER_SCHEDULER)


async def poll_job() -> None:
    """Entry point registered with APScheduler. Never raises: any failure is
    logged and, where appropriate, converted into a router_unreachable alert,
    so one bad poll never crashes the scheduler loop (APScheduler is also
    configured with max_instances=1 so a slow poll can't overlap the next)."""
    try:
        async with AsyncSessionLocal() as db:
            await _poll_once(db)
    except Exception:  # noqa: BLE001 - last line of defense for the poll loop
        logger.exception("Unhandled error in poll_job - poll cycle skipped")


async def _poll_once(db: AsyncSession) -> None:
    now = datetime.now(timezone.utc)
    client = await router_config_service.build_client(db)
    if client is None:
        logger.warning("Mikrotik router not configured yet - skipping poll cycle")
        return

    try:
        active = await client.list_active_connections()
        resource = await client.get_system_resource()
        secrets = await client.list_secrets()
    except (MikrotikConnectionError, MikrotikAuthError) as exc:
        state.record_failure(str(exc), now)
        logger.error("Router unreachable during poll: %s", exc)
        await alert_service.raise_alert(
            db,
            type_="router_unreachable",
            severity="critical",
            message=f"Cannot reach the Mikrotik concentrator: {exc}",
        )
        return
    except MikrotikError as exc:
        state.record_failure(str(exc), now)
        logger.error("Unexpected Mikrotik error during poll: %s", exc)
        await alert_service.raise_alert(
            db,
            type_="router_unreachable",
            severity="critical",
            message=f"Unexpected error communicating with the concentrator: {exc}",
        )
        return

    state.record_success(resource, now)
    await alert_service.resolve_open_alert_by_type(db, "router_unreachable", None, notify_recovery=True)

    active_by_name = {c.name: c for c in active}
    configured_names = {s.name for s in secrets}

    settings_row = await get_or_create_settings(db)
    threshold_seconds = settings_row.offline_threshold_minutes * 60

    peers = list((await db.execute(select(Peer))).scalars().all())

    snapshots: list[PeerStatusSnapshot] = []
    for peer in peers:
        conn = active_by_name.get(peer.name)
        is_online = conn is not None
        snapshots.append(
            PeerStatusSnapshot(
                peer_id=peer.id,
                timestamp=now,
                is_online=is_online,
                uptime_seconds=conn.uptime_seconds if conn else None,
                caller_id=conn.caller_id if conn else None,
                remote_address=conn.address if conn else None,
                tx_bytes=conn.tx_bytes if conn else None,
                rx_bytes=conn.rx_bytes if conn else None,
            )
        )

        was_online = peer.is_online
        peer.is_online = is_online

        if is_online:
            peer.last_seen_online_at = now
            if not was_online:
                await alert_service.resolve_open_alert_by_type(db, "peer_offline", peer.id, notify_recovery=True)
        elif peer.last_seen_online_at is not None:
            offline_seconds = (now - ensure_aware(peer.last_seen_online_at)).total_seconds()
            if offline_seconds >= threshold_seconds:
                minutes = int(offline_seconds // 60)
                await alert_service.raise_alert(
                    db,
                    type_="peer_offline",
                    severity="warning",
                    peer_id=peer.id,
                    message=f"Peer '{peer.name}' has been offline for {minutes} minutes.",
                )

    db.add_all(snapshots)
    await db.commit()

    missing_on_router = {p.name for p in peers} - configured_names
    if missing_on_router:
        # Configuration drift (peer exists in our DB but not on the router) is
        # logged for operator visibility. Per spec, only offline/unreachable
        # conditions raise alerts - this is not itself an outage.
        logger.warning("Peers in DB but missing on router: %s", ", ".join(sorted(missing_on_router)))


async def prune_snapshots_job() -> None:
    try:
        async with AsyncSessionLocal() as db:
            await _prune_once(db)
    except Exception:  # noqa: BLE001
        logger.exception("Unhandled error in prune_snapshots_job")


async def _prune_once(db: AsyncSession) -> None:
    settings_row = await get_or_create_settings(db)
    cutoff = datetime.now(timezone.utc) - timedelta(days=settings_row.snapshot_retention_days)
    result = await db.execute(delete(PeerStatusSnapshot).where(PeerStatusSnapshot.timestamp < cutoff))
    await db.commit()
    logger.info("Pruned %d snapshot rows older than %s", result.rowcount, cutoff.isoformat())

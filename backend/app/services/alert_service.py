from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import LOGGER_APP, get_logger
from app.core.timeutils import ensure_aware
from app.models.alert import Alert
from app.models.user import User
from app.services.notifications import dispatcher

logger = get_logger(LOGGER_APP)


class AlertNotFoundError(Exception):
    pass


async def _find_open_alert(db: AsyncSession, type_: str, peer_id: int | None) -> Alert | None:
    result = await db.execute(
        select(Alert).where(Alert.type == type_, Alert.peer_id == peer_id, Alert.resolved_at.is_(None))
    )
    return result.scalar_one_or_none()


async def raise_alert(
    db: AsyncSession,
    type_: str,
    severity: str,
    message: str,
    peer_id: int | None = None,
) -> Alert:
    """Raise (or refresh) an alert, deduplicating on (type, peer_id) while
    unresolved. A brand-new alert always notifies immediately; an already-open
    alert only re-notifies after the configured cooldown, to avoid spamming a
    channel every poll cycle while a condition persists."""
    existing = await _find_open_alert(db, type_, peer_id)
    now = datetime.now(timezone.utc)

    if existing is None:
        alert = Alert(peer_id=peer_id, type=type_, severity=severity, message=message, last_notified_at=now)
        db.add(alert)
        await db.commit()
        await db.refresh(alert)
        await dispatcher.notify_alert(db, alert)
        return alert

    existing.message = message
    existing.severity = severity
    should_notify = False
    if existing.last_notified_at is None:
        should_notify = True
    else:
        settings_row = await dispatcher.get_or_create_settings(db)
        cooldown_seconds = settings_row.router_unreachable_realert_minutes * 60
        if (now - ensure_aware(existing.last_notified_at)).total_seconds() >= cooldown_seconds:
            should_notify = True

    if should_notify:
        existing.last_notified_at = now
    await db.commit()
    await db.refresh(existing)

    if should_notify:
        await dispatcher.notify_alert(db, existing)
    return existing


async def resolve_alert(db: AsyncSession, alert_id: int, notify_recovery: bool = False) -> Alert:
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    if alert is None:
        raise AlertNotFoundError(f"Alert {alert_id} not found")
    if alert.resolved_at is None:
        alert.resolved_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(alert)
        if notify_recovery:
            recovered = Alert(
                peer_id=alert.peer_id,
                type=alert.type,
                severity="info",
                message=f"Recovered: {alert.message}",
            )
            await dispatcher.notify_alert(db, recovered)
    return alert


async def resolve_open_alert_by_type(db: AsyncSession, type_: str, peer_id: int | None, notify_recovery: bool = True) -> None:
    existing = await _find_open_alert(db, type_, peer_id)
    if existing is not None:
        await resolve_alert(db, existing.id, notify_recovery=notify_recovery)


async def acknowledge_alert(db: AsyncSession, alert_id: int, actor: User) -> Alert:
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    if alert is None:
        raise AlertNotFoundError(f"Alert {alert_id} not found")
    alert.acknowledged_by = actor.id
    alert.acknowledged_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(alert)
    return alert


async def list_alerts(db: AsyncSession, status: str = "active") -> list[Alert]:
    query = select(Alert).order_by(Alert.created_at.desc())
    if status == "active":
        query = query.where(Alert.resolved_at.is_(None))
    elif status == "resolved":
        query = query.where(Alert.resolved_at.is_not(None))
    result = await db.execute(query)
    return list(result.scalars().all())


async def count_active_alerts(db: AsyncSession) -> int:
    from sqlalchemy import func

    result = await db.execute(select(func.count()).select_from(Alert).where(Alert.resolved_at.is_(None)))
    return result.scalar_one()

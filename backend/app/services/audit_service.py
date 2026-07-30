from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.models.user import User

_REDACTED_KEYS = {"password", "api_secret", "encrypted_password", "encrypted_secret"}


def _redact(data: dict[str, Any] | None) -> dict[str, Any] | None:
    if data is None:
        return None
    return {k: ("***" if k in _REDACTED_KEYS and v is not None else v) for k, v in data.items()}


async def record(
    db: AsyncSession,
    actor: User | None,
    action: str,
    target_peer_id: int | None = None,
    before: dict[str, Any] | None = None,
    after: dict[str, Any] | None = None,
    ip_address: str | None = None,
) -> AuditLog:
    entry = AuditLog(
        user_id=actor.id if actor else None,
        action=action,
        target_peer_id=target_peer_id,
        before_json=_redact(before),
        after_json=_redact(after),
        ip_address=ip_address,
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry


async def list_audit_log(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 50,
    user_id: int | None = None,
    action: str | None = None,
    peer_id: int | None = None,
) -> tuple[list[AuditLog], int]:
    query = select(AuditLog)
    count_query = select(func.count()).select_from(AuditLog)
    if user_id is not None:
        query = query.where(AuditLog.user_id == user_id)
        count_query = count_query.where(AuditLog.user_id == user_id)
    if action is not None:
        query = query.where(AuditLog.action == action)
        count_query = count_query.where(AuditLog.action == action)
    if peer_id is not None:
        query = query.where(AuditLog.target_peer_id == peer_id)
        count_query = count_query.where(AuditLog.target_peer_id == peer_id)

    total = (await db.execute(count_query)).scalar_one()
    query = query.order_by(AuditLog.timestamp.desc()).offset((page - 1) * page_size).limit(page_size)
    rows = list((await db.execute(query)).scalars().all())
    return rows, total


async def get_user_map(db: AsyncSession, user_ids: set[int]) -> dict[int, str]:
    if not user_ids:
        return {}
    result = await db.execute(select(User.id, User.username).where(User.id.in_(user_ids)))
    return {row.id: row.username for row in result.all()}

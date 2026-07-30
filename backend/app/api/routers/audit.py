from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import require_role
from app.models.peer import Peer
from app.schemas.audit import AuditLogOut
from app.schemas.common import PaginatedResponse
from app.services import audit_service

router = APIRouter(prefix="/audit", tags=["audit"], dependencies=[Depends(require_role("admin"))])


@router.get("", response_model=PaginatedResponse[AuditLogOut])
async def list_audit_log(
    user_id: int | None = None,
    action: str | None = None,
    peer_id: int | None = None,
    page: int = 1,
    page_size: int = 50,
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[AuditLogOut]:
    rows, total = await audit_service.list_audit_log(
        db, page=page, page_size=page_size, user_id=user_id, action=action, peer_id=peer_id
    )

    user_ids = {r.user_id for r in rows if r.user_id is not None}
    user_map = await audit_service.get_user_map(db, user_ids)

    peer_ids = {r.target_peer_id for r in rows if r.target_peer_id is not None}
    peer_map: dict[int, str] = {}
    if peer_ids:
        result = await db.execute(select(Peer.id, Peer.name).where(Peer.id.in_(peer_ids)))
        peer_map = {row.id: row.name for row in result.all()}

    items = [
        AuditLogOut(
            id=r.id,
            user_id=r.user_id,
            username=user_map.get(r.user_id) if r.user_id else None,
            action=r.action,
            target_peer_id=r.target_peer_id,
            peer_name=peer_map.get(r.target_peer_id) if r.target_peer_id else None,
            before_json=r.before_json,
            after_json=r.after_json,
            ip_address=r.ip_address,
            timestamp=r.timestamp,
        )
        for r in rows
    ]
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size)

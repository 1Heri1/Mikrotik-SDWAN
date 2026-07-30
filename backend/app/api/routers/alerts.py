from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.models.alert import Alert
from app.models.peer import Peer
from app.models.user import User
from app.schemas.alert import AlertOut
from app.services import alert_service
from app.services.alert_service import AlertNotFoundError

router = APIRouter(prefix="/alerts", tags=["alerts"])


async def _to_out(db: AsyncSession, alerts: list[Alert]) -> list[AlertOut]:
    peer_ids = {a.peer_id for a in alerts if a.peer_id is not None}
    peer_map: dict[int, str] = {}
    if peer_ids:
        result = await db.execute(select(Peer.id, Peer.name).where(Peer.id.in_(peer_ids)))
        peer_map = {row.id: row.name for row in result.all()}

    user_ids = {a.acknowledged_by for a in alerts if a.acknowledged_by is not None}
    user_map: dict[int, str] = {}
    if user_ids:
        result = await db.execute(select(User.id, User.username).where(User.id.in_(user_ids)))
        user_map = {row.id: row.username for row in result.all()}

    return [
        AlertOut(
            id=a.id,
            peer_id=a.peer_id,
            peer_name=peer_map.get(a.peer_id) if a.peer_id else None,
            type=a.type,
            severity=a.severity,
            message=a.message,
            created_at=a.created_at,
            resolved_at=a.resolved_at,
            acknowledged_by=a.acknowledged_by,
            acknowledged_by_username=user_map.get(a.acknowledged_by) if a.acknowledged_by else None,
            acknowledged_at=a.acknowledged_at,
        )
        for a in alerts
    ]


@router.get("", response_model=list[AlertOut], dependencies=[Depends(get_current_user)])
async def list_alerts(status_: str = "active", db: AsyncSession = Depends(get_db)) -> list[AlertOut]:
    alerts = await alert_service.list_alerts(db, status=status_)
    return await _to_out(db, alerts)


@router.post("/{alert_id}/acknowledge", response_model=AlertOut)
async def acknowledge_alert(
    alert_id: int, db: AsyncSession = Depends(get_db), actor: User = Depends(get_current_user)
) -> AlertOut:
    try:
        alert = await alert_service.acknowledge_alert(db, alert_id, actor)
    except AlertNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    return (await _to_out(db, [alert]))[0]


@router.post("/{alert_id}/resolve", response_model=AlertOut)
async def resolve_alert(
    alert_id: int, db: AsyncSession = Depends(get_db), _: User = Depends(require_role("admin"))
) -> AlertOut:
    try:
        alert = await alert_service.resolve_alert(db, alert_id)
    except AlertNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    return (await _to_out(db, [alert]))[0]

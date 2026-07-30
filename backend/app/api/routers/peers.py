from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.models.peer import Peer
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.peer import (
    DiffPreview,
    GeneratedPassword,
    PeerCreate,
    PeerHistoryPoint,
    PeerOut,
    PeerUpdate,
    RevealedPassword,
)
from app.services import peer_service, router_config_service
from app.services.mikrotik.base import MikrotikBackend
from app.services.peer_service import PeerNotFoundError
from app.utils.password_gen import generate_strong_password

router = APIRouter(prefix="/peers", tags=["peers"])


async def _get_client(db: AsyncSession) -> MikrotikBackend:
    client = await router_config_service.build_client(db)
    if client is None:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "Mikrotik router is not configured yet. Set it up in Settings first.",
        )
    return client


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.get("", response_model=PaginatedResponse[PeerOut], dependencies=[Depends(get_current_user)])
async def list_peers(
    search: str | None = None,
    status_filter: Literal["online", "offline"] | None = None,
    profile: str | None = None,
    page: int = 1,
    page_size: int = 50,
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[PeerOut]:
    return await peer_service.list_peers(
        db, search=search, status_filter=status_filter, profile_filter=profile, page=page, page_size=page_size
    )


@router.get("/generate-password", response_model=GeneratedPassword)
async def generate_password(_: User = Depends(require_role("admin"))) -> GeneratedPassword:
    return GeneratedPassword(password=generate_strong_password())


@router.get("/{peer_id}", response_model=PeerOut, dependencies=[Depends(get_current_user)])
async def get_peer(peer_id: int, db: AsyncSession = Depends(get_db)) -> Peer:
    try:
        return await peer_service.get_peer_or_raise(db, peer_id)
    except PeerNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc


@router.get(
    "/{peer_id}/history",
    response_model=list[PeerHistoryPoint],
    dependencies=[Depends(get_current_user)],
)
async def get_peer_history(
    peer_id: int, range: Literal["24h", "7d", "30d"] = "24h", db: AsyncSession = Depends(get_db)
) -> list[PeerHistoryPoint]:
    rows = await peer_service.get_peer_history(db, peer_id, range)
    return [PeerHistoryPoint.model_validate(r) for r in rows]


@router.post("", response_model=PeerOut, status_code=status.HTTP_201_CREATED)
async def create_peer(
    body: PeerCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: User = Depends(require_role("admin")),
) -> Peer:
    client = await _get_client(db)
    return await peer_service.create_peer(db, body, client, actor, ip_address=_client_ip(request))


@router.post("/{peer_id}/preview", response_model=DiffPreview)
async def preview_peer_update(
    peer_id: int, body: PeerUpdate, db: AsyncSession = Depends(get_db), _: User = Depends(require_role("admin"))
) -> DiffPreview:
    try:
        return await peer_service.preview_update(db, peer_id, body)
    except PeerNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc


@router.patch("/{peer_id}", response_model=PeerOut)
async def update_peer(
    peer_id: int,
    body: PeerUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: User = Depends(require_role("admin")),
) -> Peer:
    client = await _get_client(db)
    try:
        return await peer_service.update_peer(db, peer_id, body, client, actor, ip_address=_client_ip(request))
    except PeerNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc


@router.post("/{peer_id}/enable", response_model=PeerOut)
async def enable_peer(
    peer_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: User = Depends(require_role("admin")),
) -> Peer:
    client = await _get_client(db)
    try:
        return await peer_service.set_enabled(db, peer_id, True, client, actor, ip_address=_client_ip(request))
    except PeerNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc


@router.post("/{peer_id}/disable", response_model=PeerOut)
async def disable_peer(
    peer_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: User = Depends(require_role("admin")),
) -> Peer:
    client = await _get_client(db)
    try:
        return await peer_service.set_enabled(db, peer_id, False, client, actor, ip_address=_client_ip(request))
    except PeerNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc


@router.post("/{peer_id}/reset-password", response_model=PeerOut)
async def reset_peer_password(
    peer_id: int,
    request: Request,
    new_password: str | None = None,
    db: AsyncSession = Depends(get_db),
    actor: User = Depends(require_role("admin")),
) -> Peer:
    client = await _get_client(db)
    try:
        return await peer_service.reset_password(
            db, peer_id, client, actor, new_password=new_password, ip_address=_client_ip(request)
        )
    except PeerNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc


@router.get("/{peer_id}/reveal-password", response_model=RevealedPassword)
async def reveal_peer_password(
    peer_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: User = Depends(require_role("admin")),
) -> RevealedPassword:
    try:
        password = await peer_service.reveal_password(db, peer_id, actor, ip_address=_client_ip(request))
    except PeerNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    return RevealedPassword(password=password)


@router.delete("/{peer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_peer(
    peer_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: User = Depends(require_role("admin")),
) -> None:
    client = await _get_client(db)
    try:
        await peer_service.delete_peer(db, peer_id, client, actor, ip_address=_client_ip(request))
    except PeerNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc

from datetime import datetime, timedelta, timezone
from typing import Literal

from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.crypto import encrypt_secret
from app.models.peer import Peer
from app.models.peer_status_snapshot import PeerStatusSnapshot
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.peer import DiffPreview, PeerCreate, PeerOut, PeerUpdate
from app.services import audit_service
from app.services.mikrotik.base import MikrotikBackend
from app.services.mikrotik.exceptions import MikrotikNotFoundError
from app.utils.password_gen import generate_strong_password

_EDITABLE_FIELDS = ("mikrotik_profile", "assigned_local_address", "assigned_remote_address", "comment")


class PeerNotFoundError(Exception):
    pass


async def get_peer_or_raise(db: AsyncSession, peer_id: int) -> Peer:
    result = await db.execute(select(Peer).where(Peer.id == peer_id))
    peer = result.scalar_one_or_none()
    if peer is None:
        raise PeerNotFoundError(f"Peer {peer_id} not found")
    return peer


async def list_peers(
    db: AsyncSession,
    search: str | None = None,
    status_filter: Literal["online", "offline"] | None = None,
    profile_filter: str | None = None,
    page: int = 1,
    page_size: int = 50,
) -> PaginatedResponse[PeerOut]:
    query = select(Peer)
    count_query = select(func.count()).select_from(Peer)

    if search:
        like = f"%{search}%"
        cond = or_(Peer.name.ilike(like), Peer.comment.ilike(like))
        query = query.where(cond)
        count_query = count_query.where(cond)
    if status_filter == "online":
        query = query.where(Peer.is_online.is_(True))
        count_query = count_query.where(Peer.is_online.is_(True))
    elif status_filter == "offline":
        query = query.where(Peer.is_online.is_(False))
        count_query = count_query.where(Peer.is_online.is_(False))
    if profile_filter:
        query = query.where(Peer.mikrotik_profile == profile_filter)
        count_query = count_query.where(Peer.mikrotik_profile == profile_filter)

    total = (await db.execute(count_query)).scalar_one()
    query = query.order_by(Peer.name).offset((page - 1) * page_size).limit(page_size)
    rows = list((await db.execute(query)).scalars().all())

    return PaginatedResponse(
        items=[PeerOut.model_validate(r) for r in rows], total=total, page=page, page_size=page_size
    )


async def get_peer_history(
    db: AsyncSession, peer_id: int, range_: Literal["24h", "7d", "30d"] = "24h"
) -> list[PeerStatusSnapshot]:
    delta = {"24h": timedelta(hours=24), "7d": timedelta(days=7), "30d": timedelta(days=30)}[range_]
    since = datetime.now(timezone.utc) - delta
    result = await db.execute(
        select(PeerStatusSnapshot)
        .where(PeerStatusSnapshot.peer_id == peer_id, PeerStatusSnapshot.timestamp >= since)
        .order_by(PeerStatusSnapshot.timestamp.asc())
    )
    return list(result.scalars().all())


async def create_peer(
    db: AsyncSession, data: PeerCreate, client: MikrotikBackend, actor: User, ip_address: str | None = None
) -> Peer:
    secret = await client.add_secret(
        name=data.name,
        password=data.password,
        profile=data.mikrotik_profile,
        service=data.service,
        local_address=data.assigned_local_address,
        remote_address=data.assigned_remote_address,
        comment=data.comment,
    )

    peer = Peer(
        name=data.name,
        encrypted_password=encrypt_secret(data.password),
        mikrotik_profile=data.mikrotik_profile,
        service=data.service,
        assigned_local_address=data.assigned_local_address,
        assigned_remote_address=data.assigned_remote_address,
        comment=data.comment,
        enabled=not secret.disabled,
        mikrotik_secret_id=secret.id or None,
    )
    db.add(peer)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise
    await db.refresh(peer)

    await audit_service.record(
        db,
        actor,
        action="peer.create",
        target_peer_id=peer.id,
        after={
            "name": peer.name,
            "mikrotik_profile": peer.mikrotik_profile,
            "service": peer.service,
            "assigned_local_address": peer.assigned_local_address,
            "assigned_remote_address": peer.assigned_remote_address,
            "comment": peer.comment,
        },
        ip_address=ip_address,
    )
    return peer


def _proposed_changes(peer: Peer, data: PeerUpdate) -> dict[str, dict[str, object]]:
    changes: dict[str, dict[str, object]] = {}
    for field in _EDITABLE_FIELDS:
        new_value = getattr(data, field)
        if new_value is not None and new_value != getattr(peer, field):
            changes[field] = {"before": getattr(peer, field), "after": new_value}
    if data.password:
        changes["password"] = {"before": "***", "after": "***"}
    return changes


async def preview_update(db: AsyncSession, peer_id: int, data: PeerUpdate) -> DiffPreview:
    peer = await get_peer_or_raise(db, peer_id)
    changes = _proposed_changes(peer, data)
    return DiffPreview(changes=changes, has_changes=bool(changes))


async def update_peer(
    db: AsyncSession,
    peer_id: int,
    data: PeerUpdate,
    client: MikrotikBackend,
    actor: User,
    ip_address: str | None = None,
) -> Peer:
    peer = await get_peer_or_raise(db, peer_id)
    changes = _proposed_changes(peer, data)
    before = {k: v["before"] for k, v in changes.items()}

    router_fields = {
        "profile": data.mikrotik_profile,
        "local_address": data.assigned_local_address,
        "remote_address": data.assigned_remote_address,
        "comment": data.comment,
    }
    if data.password:
        router_fields["password"] = data.password
    router_fields = {k: v for k, v in router_fields.items() if v is not None}

    if router_fields:
        await client.edit_secret(peer.name, **router_fields)

    if data.mikrotik_profile is not None:
        peer.mikrotik_profile = data.mikrotik_profile
    if data.assigned_local_address is not None:
        peer.assigned_local_address = data.assigned_local_address
    if data.assigned_remote_address is not None:
        peer.assigned_remote_address = data.assigned_remote_address
    if data.comment is not None:
        peer.comment = data.comment
    if data.password:
        peer.encrypted_password = encrypt_secret(data.password)

    await db.commit()
    await db.refresh(peer)

    after = {k: getattr(peer, k) if k != "password" else "***" for k in changes}
    await audit_service.record(
        db, actor, action="peer.update", target_peer_id=peer.id, before=before, after=after, ip_address=ip_address
    )
    return peer


async def set_enabled(
    db: AsyncSession, peer_id: int, enabled: bool, client: MikrotikBackend, actor: User, ip_address: str | None = None
) -> Peer:
    peer = await get_peer_or_raise(db, peer_id)
    before_enabled = peer.enabled
    await client.set_secret_enabled(peer.name, enabled)
    peer.enabled = enabled
    await db.commit()
    await db.refresh(peer)

    await audit_service.record(
        db,
        actor,
        action="peer.enable" if enabled else "peer.disable",
        target_peer_id=peer.id,
        before={"enabled": before_enabled},
        after={"enabled": enabled},
        ip_address=ip_address,
    )
    return peer


async def delete_peer(
    db: AsyncSession, peer_id: int, client: MikrotikBackend, actor: User, ip_address: str | None = None
) -> None:
    peer = await get_peer_or_raise(db, peer_id)
    try:
        await client.delete_secret(peer.name)
    except MikrotikNotFoundError:
        # Already gone on the router - proceed with removing our DB record too.
        pass

    await audit_service.record(
        db,
        actor,
        action="peer.delete",
        target_peer_id=None,  # row is about to be deleted; keep the log entry orphan-safe
        before={"name": peer.name, "mikrotik_profile": peer.mikrotik_profile},
        ip_address=ip_address,
    )
    await db.delete(peer)
    await db.commit()


async def reset_password(
    db: AsyncSession,
    peer_id: int,
    client: MikrotikBackend,
    actor: User,
    new_password: str | None = None,
    ip_address: str | None = None,
) -> Peer:
    peer = await get_peer_or_raise(db, peer_id)
    password = new_password or generate_strong_password()
    await client.edit_secret(peer.name, password=password)
    peer.encrypted_password = encrypt_secret(password)
    await db.commit()
    await db.refresh(peer)

    await audit_service.record(
        db,
        actor,
        action="peer.reset_password",
        target_peer_id=peer.id,
        before={"password": "***"},
        after={"password": "***"},
        ip_address=ip_address,
    )
    return peer


async def reveal_password(db: AsyncSession, peer_id: int, actor: User, ip_address: str | None = None) -> str:
    from app.core.crypto import decrypt_secret

    peer = await get_peer_or_raise(db, peer_id)
    await audit_service.record(
        db, actor, action="peer.reveal_password", target_peer_id=peer.id, ip_address=ip_address
    )
    return decrypt_secret(peer.encrypted_password)

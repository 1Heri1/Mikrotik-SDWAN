from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.crypto import decrypt_secret, encrypt_secret
from app.models.router_config import RouterConfig
from app.schemas.router_config import RouterConfigUpdate
from app.services.mikrotik.base import MikrotikBackend
from app.services.mikrotik.factory import MikrotikConnectionConfig, get_mikrotik_client

_SINGLETON_ID = 1


async def get_active_config(db: AsyncSession) -> RouterConfig | None:
    result = await db.execute(select(RouterConfig).where(RouterConfig.id == _SINGLETON_ID))
    return result.scalar_one_or_none()


async def upsert_config(db: AsyncSession, data: RouterConfigUpdate) -> RouterConfig:
    row = await get_active_config(db)
    if row is None:
        if not data.api_secret:
            raise ValueError("api_secret is required when configuring the router for the first time")
        row = RouterConfig(
            id=_SINGLETON_ID,
            host=data.host,
            port=data.port,
            api_user=data.api_user,
            encrypted_secret=encrypt_secret(data.api_secret),
            protocol=data.protocol,
            verify_ssl=data.verify_ssl,
            backup_before_bulk_ops=data.backup_before_bulk_ops,
        )
        db.add(row)
    else:
        row.host = data.host
        row.port = data.port
        row.api_user = data.api_user
        row.protocol = data.protocol
        row.verify_ssl = data.verify_ssl
        row.backup_before_bulk_ops = data.backup_before_bulk_ops
        if data.api_secret:
            row.encrypted_secret = encrypt_secret(data.api_secret)
    await db.commit()
    await db.refresh(row)
    return row


def _connection_config_from_row(row: RouterConfig) -> MikrotikConnectionConfig:
    return MikrotikConnectionConfig(
        host=row.host,
        port=row.port,
        api_user=row.api_user,
        secret=decrypt_secret(row.encrypted_secret),
        protocol=row.protocol,  # type: ignore[arg-type]
        verify_ssl=row.verify_ssl,
    )


def _connection_config_from_settings() -> MikrotikConnectionConfig | None:
    """Bootstrap fallback used before an admin has saved a router config in
    Settings, so the first poll after a fresh install still works if the
    operator filled in the Mikrotik .env variables."""
    settings = get_settings()
    if not settings.MIKROTIK_HOST or not settings.MIKROTIK_API_USER:
        return None
    return MikrotikConnectionConfig(
        host=settings.MIKROTIK_HOST,
        port=settings.MIKROTIK_PORT,
        api_user=settings.MIKROTIK_API_USER,
        secret=settings.MIKROTIK_API_PASSWORD,
        protocol=settings.MIKROTIK_BACKEND,
        verify_ssl=settings.MIKROTIK_VERIFY_SSL,
    )


async def build_client(db: AsyncSession) -> MikrotikBackend | None:
    """Return a configured MikrotikBackend, or None if nothing is configured yet
    (neither a DB row nor .env fallback values)."""
    row = await get_active_config(db)
    cfg = _connection_config_from_row(row) if row is not None else _connection_config_from_settings()
    if cfg is None:
        return None
    return get_mikrotik_client(cfg)

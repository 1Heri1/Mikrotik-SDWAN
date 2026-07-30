from dataclasses import dataclass
from typing import Literal

from app.services.mikrotik.base import MikrotikBackend
from app.services.mikrotik.librouteros_backend import LibrouterosBackend
from app.services.mikrotik.rest_backend import RestApiBackend


@dataclass
class MikrotikConnectionConfig:
    """Backend-agnostic connection details, built either from the DB
    router_config row (admin-editable, takes precedence) or from .env
    fallback values before an admin has configured the router in Settings."""

    host: str
    port: int
    api_user: str
    secret: str  # decrypted password / API key, never persisted in this shape
    protocol: Literal["librouteros", "rest"]
    verify_ssl: bool = True


def get_mikrotik_client(cfg: MikrotikConnectionConfig) -> MikrotikBackend:
    if cfg.protocol == "librouteros":
        return LibrouterosBackend(host=cfg.host, port=cfg.port, username=cfg.api_user, password=cfg.secret)
    if cfg.protocol == "rest":
        return RestApiBackend(
            host=cfg.host,
            port=cfg.port,
            username=cfg.api_user,
            password=cfg.secret,
            verify_ssl=cfg.verify_ssl,
        )
    raise ValueError(f"Unknown Mikrotik protocol: {cfg.protocol!r}")

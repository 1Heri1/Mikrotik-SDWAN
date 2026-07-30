"""Import every model module so Base.metadata is complete for Alembic autogeneration."""

from app.models.base import Base
from app.models.user import User
from app.models.refresh_token import RefreshToken
from app.models.peer import Peer
from app.models.peer_status_snapshot import PeerStatusSnapshot
from app.models.alert import Alert
from app.models.audit_log import AuditLog
from app.models.router_config import RouterConfig
from app.models.notification_settings import NotificationSettings

__all__ = [
    "Base",
    "User",
    "RefreshToken",
    "Peer",
    "PeerStatusSnapshot",
    "Alert",
    "AuditLog",
    "RouterConfig",
    "NotificationSettings",
]

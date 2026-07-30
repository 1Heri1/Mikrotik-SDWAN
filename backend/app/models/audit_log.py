from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

# JSONB on Postgres (production), generic JSON everywhere else (e.g. SQLite
# in tests) - same pattern used consistently so the test suite doesn't need
# a live Postgres instance just to exercise audit log read/write paths.
_JSON_TYPE = JSON().with_variant(JSONB(), "postgresql")


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    target_peer_id: Mapped[int | None] = mapped_column(
        ForeignKey("peers.id", ondelete="SET NULL"), nullable=True
    )
    before_json: Mapped[dict | None] = mapped_column(_JSON_TYPE, default=None)
    after_json: Mapped[dict | None] = mapped_column(_JSON_TYPE, default=None)
    ip_address: Mapped[str | None] = mapped_column(String(45), default=None)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True, nullable=False
    )

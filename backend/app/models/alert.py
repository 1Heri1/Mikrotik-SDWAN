from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Alert(Base):
    __tablename__ = "alerts"
    __table_args__ = (
        # Speeds up the "is there already an open alert of this type for this
        # peer" dedup check performed on every poll cycle.
        Index(
            "ix_alerts_unresolved",
            "type",
            "peer_id",
            postgresql_where=text("resolved_at IS NULL"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    peer_id: Mapped[int | None] = mapped_column(
        ForeignKey("peers.id", ondelete="SET NULL"), nullable=True, index=True
    )
    type: Mapped[str] = mapped_column(String(32), nullable=False)  # peer_offline | router_unreachable | login_failures
    severity: Mapped[str] = mapped_column(String(16), nullable=False)  # info | warning | critical
    message: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True, nullable=False
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    acknowledged_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    last_notified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)

    peer: Mapped["Peer | None"] = relationship(back_populates="alerts")

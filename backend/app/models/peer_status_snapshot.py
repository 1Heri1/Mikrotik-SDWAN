from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class PeerStatusSnapshot(Base):
    """One poll cycle's observed status for a single peer.

    Historized (not just latest-state) so the dashboard can render
    availability-over-time charts for 24h / 7d / 30d ranges. Rows older than
    SNAPSHOT_RETENTION_DAYS are pruned nightly by the scheduler.
    """

    __tablename__ = "peer_status_snapshots"
    __table_args__ = (Index("ix_snapshot_peer_ts", "peer_id", "timestamp"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    peer_id: Mapped[int] = mapped_column(
        ForeignKey("peers.id", ondelete="CASCADE"), index=True, nullable=False
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), index=True, server_default=func.now(), nullable=False
    )
    is_online: Mapped[bool] = mapped_column(Boolean, nullable=False)
    uptime_seconds: Mapped[int | None] = mapped_column(default=None)
    caller_id: Mapped[str | None] = mapped_column(String(64), default=None)
    remote_address: Mapped[str | None] = mapped_column(String(64), default=None)
    tx_bytes: Mapped[int | None] = mapped_column(BigInteger(), default=None)
    rx_bytes: Mapped[int | None] = mapped_column(BigInteger(), default=None)

    peer: Mapped["Peer"] = relationship(back_populates="snapshots")

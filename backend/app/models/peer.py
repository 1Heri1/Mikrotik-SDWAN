from datetime import datetime

from sqlalchemy import Boolean, DateTime, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Peer(Base, TimestampMixin):
    """A configured PPP secret (VPN peer) on the Mikrotik concentrator."""

    __tablename__ = "peers"
    __table_args__ = (Index("ix_peers_enabled", "enabled"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    encrypted_password: Mapped[str] = mapped_column(Text, nullable=False)
    mikrotik_profile: Mapped[str] = mapped_column(String(64), nullable=False)
    service: Mapped[str] = mapped_column(String(16), default="pptp", nullable=False)  # pptp | l2tp
    assigned_local_address: Mapped[str | None] = mapped_column(String(64), default=None)
    assigned_remote_address: Mapped[str | None] = mapped_column(String(64), default=None)
    comment: Mapped[str | None] = mapped_column(String(255), default=None)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    mikrotik_secret_id: Mapped[str | None] = mapped_column(String(32), default=None)
    last_seen_online_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    # Denormalized cache of "is this peer online as of the latest poll cycle",
    # updated by the scheduler alongside each snapshot insert. Avoids a
    # correlated "latest snapshot per peer" subquery on every peers-list
    # request; full history still lives in peer_status_snapshots.
    is_online: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    snapshots: Mapped[list["PeerStatusSnapshot"]] = relationship(
        back_populates="peer", cascade="all, delete-orphan"
    )
    alerts: Mapped[list["Alert"]] = relationship(back_populates="peer")

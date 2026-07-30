from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class NotificationSettings(Base):
    """Live, admin-editable notification channels and alert thresholds.

    Kept in the DB (rather than only .env) so changes made from the Settings
    page take effect immediately, without a backend restart.
    """

    __tablename__ = "notification_settings"

    id: Mapped[int] = mapped_column(primary_key=True)

    telegram_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    telegram_bot_token_encrypted: Mapped[str | None] = mapped_column(Text, default=None)
    telegram_chat_id: Mapped[str | None] = mapped_column(String(64), default=None)

    smtp_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    smtp_host: Mapped[str | None] = mapped_column(String(255), default=None)
    smtp_port: Mapped[int | None] = mapped_column(default=None)
    smtp_username: Mapped[str | None] = mapped_column(String(255), default=None)
    smtp_password_encrypted: Mapped[str | None] = mapped_column(Text, default=None)
    smtp_from_address: Mapped[str | None] = mapped_column(String(255), default=None)
    smtp_to_address: Mapped[str | None] = mapped_column(String(255), default=None)
    smtp_use_tls: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    offline_threshold_minutes: Mapped[int] = mapped_column(default=10, nullable=False)
    router_unreachable_realert_minutes: Mapped[int] = mapped_column(default=30, nullable=False)
    snapshot_retention_days: Mapped[int] = mapped_column(default=30, nullable=False)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

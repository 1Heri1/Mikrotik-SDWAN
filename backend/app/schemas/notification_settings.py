from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class NotificationSettingsOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    telegram_enabled: bool
    telegram_chat_id: str | None
    telegram_token_configured: bool
    smtp_enabled: bool
    smtp_host: str | None
    smtp_port: int | None
    smtp_username: str | None
    smtp_password_configured: bool
    smtp_from_address: str | None
    smtp_to_address: str | None
    smtp_use_tls: bool
    offline_threshold_minutes: int
    router_unreachable_realert_minutes: int
    snapshot_retention_days: int
    updated_at: datetime


class NotificationSettingsUpdate(BaseModel):
    telegram_enabled: bool = False
    telegram_bot_token: str | None = Field(default=None, description="Omit to keep the stored token")
    telegram_chat_id: str | None = None

    smtp_enabled: bool = False
    smtp_host: str | None = None
    smtp_port: int | None = Field(default=587, ge=1, le=65535)
    smtp_username: str | None = None
    smtp_password: str | None = Field(default=None, description="Omit to keep the stored password")
    smtp_from_address: str | None = None
    smtp_to_address: str | None = None
    smtp_use_tls: bool = True

    offline_threshold_minutes: int = Field(default=10, ge=1, le=1440)
    router_unreachable_realert_minutes: int = Field(default=30, ge=1, le=1440)
    snapshot_retention_days: int = Field(default=30, ge=1, le=365)


class TestTelegramRequest(BaseModel):
    bot_token: str | None = Field(default=None, description="Omit to use the currently stored token")
    chat_id: str | None = Field(default=None, description="Omit to use the currently stored chat id")


class TestNotificationResult(BaseModel):
    success: bool
    message: str

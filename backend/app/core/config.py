from functools import lru_cache
from typing import Literal

from cryptography.fernet import Fernet
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration, loaded from environment variables / .env.

    These are only defaults / bootstrap values. Several of them (Mikrotik
    router connection, notification channels, alert thresholds) are shadowed
    by live, admin-editable rows in the database once an admin has visited
    the Settings page - see services/router_config_service.py and
    services/notifications/dispatcher.py.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ENV: Literal["dev", "prod"] = "prod"
    LOG_DIR: str = "./logs"

    # Database
    DATABASE_URL: str

    # JWT / sessions
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Encryption at rest
    FERNET_KEY: str

    # CORS
    CORS_ORIGINS: str = "https://localhost"

    # Mikrotik bootstrap / fallback config
    MIKROTIK_BACKEND: Literal["librouteros", "rest"] = "librouteros"
    MIKROTIK_HOST: str = ""
    MIKROTIK_PORT: int = 8728
    MIKROTIK_API_USER: str = ""
    MIKROTIK_API_PASSWORD: str = ""
    MIKROTIK_USE_SSL_REST: bool = True
    MIKROTIK_VERIFY_SSL: bool = True

    # Scheduler / alerting bootstrap defaults
    POLL_INTERVAL_SECONDS: int = 60
    OFFLINE_ALERT_THRESHOLD_MINUTES: int = 10
    ROUTER_UNREACHABLE_REALERT_MINUTES: int = 30
    SNAPSHOT_RETENTION_DAYS: int = 30

    # Telegram bootstrap defaults
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""

    # SMTP bootstrap defaults
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_ADDRESS: str = ""
    SMTP_TO_ADDRESS: str = ""
    SMTP_USE_TLS: bool = True

    @field_validator("FERNET_KEY")
    @classmethod
    def _validate_fernet_key(cls, v: str) -> str:
        try:
            Fernet(v.encode())
        except Exception as exc:  # noqa: BLE001 - re-raised with clearer message
            raise ValueError(
                "FERNET_KEY is not a valid Fernet key. Generate one with: "
                "python -c \"from cryptography.fernet import Fernet; "
                'print(Fernet.generate_key().decode())"'
            ) from exc
        return v

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]

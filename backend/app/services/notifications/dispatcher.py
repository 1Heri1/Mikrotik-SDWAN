from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.crypto import decrypt_secret, encrypt_secret
from app.core.logging import LOGGER_APP, get_logger
from app.models.alert import Alert
from app.models.notification_settings import NotificationSettings
from app.schemas.notification_settings import NotificationSettingsUpdate
from app.services.notifications.base import NotificationChannel
from app.services.notifications.email_smtp import SmtpNotifier
from app.services.notifications.telegram import TelegramNotifier

logger = get_logger(LOGGER_APP)

_SINGLETON_ID = 1


async def get_or_create_settings(db: AsyncSession) -> NotificationSettings:
    """Return the single live NotificationSettings row, creating it (seeded
    from .env bootstrap defaults) on first access."""
    result = await db.execute(select(NotificationSettings).where(NotificationSettings.id == _SINGLETON_ID))
    row = result.scalar_one_or_none()
    if row is not None:
        return row

    bootstrap = get_settings()
    row = NotificationSettings(
        id=_SINGLETON_ID,
        telegram_enabled=bool(bootstrap.TELEGRAM_BOT_TOKEN and bootstrap.TELEGRAM_CHAT_ID),
        telegram_bot_token_encrypted=(
            encrypt_secret(bootstrap.TELEGRAM_BOT_TOKEN) if bootstrap.TELEGRAM_BOT_TOKEN else None
        ),
        telegram_chat_id=bootstrap.TELEGRAM_CHAT_ID or None,
        smtp_enabled=bool(bootstrap.SMTP_HOST and bootstrap.SMTP_FROM_ADDRESS and bootstrap.SMTP_TO_ADDRESS),
        smtp_host=bootstrap.SMTP_HOST or None,
        smtp_port=bootstrap.SMTP_PORT,
        smtp_username=bootstrap.SMTP_USERNAME or None,
        smtp_password_encrypted=encrypt_secret(bootstrap.SMTP_PASSWORD) if bootstrap.SMTP_PASSWORD else None,
        smtp_from_address=bootstrap.SMTP_FROM_ADDRESS or None,
        smtp_to_address=bootstrap.SMTP_TO_ADDRESS or None,
        smtp_use_tls=bootstrap.SMTP_USE_TLS,
        offline_threshold_minutes=bootstrap.OFFLINE_ALERT_THRESHOLD_MINUTES,
        router_unreachable_realert_minutes=bootstrap.ROUTER_UNREACHABLE_REALERT_MINUTES,
        snapshot_retention_days=bootstrap.SNAPSHOT_RETENTION_DAYS,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def update_settings(db: AsyncSession, data: NotificationSettingsUpdate) -> NotificationSettings:
    row = await get_or_create_settings(db)

    row.telegram_enabled = data.telegram_enabled
    if data.telegram_bot_token:
        row.telegram_bot_token_encrypted = encrypt_secret(data.telegram_bot_token)
    row.telegram_chat_id = data.telegram_chat_id

    row.smtp_enabled = data.smtp_enabled
    row.smtp_host = data.smtp_host
    row.smtp_port = data.smtp_port
    row.smtp_username = data.smtp_username
    if data.smtp_password:
        row.smtp_password_encrypted = encrypt_secret(data.smtp_password)
    row.smtp_from_address = data.smtp_from_address
    row.smtp_to_address = data.smtp_to_address
    row.smtp_use_tls = data.smtp_use_tls

    row.offline_threshold_minutes = data.offline_threshold_minutes
    row.router_unreachable_realert_minutes = data.router_unreachable_realert_minutes
    row.snapshot_retention_days = data.snapshot_retention_days

    await db.commit()
    await db.refresh(row)
    return row


async def _build_channels(settings_row: NotificationSettings) -> list[NotificationChannel]:
    channels: list[NotificationChannel] = []
    if settings_row.telegram_enabled and settings_row.telegram_bot_token_encrypted and settings_row.telegram_chat_id:
        channels.append(
            TelegramNotifier(
                bot_token=decrypt_secret(settings_row.telegram_bot_token_encrypted),
                chat_id=settings_row.telegram_chat_id,
            )
        )
    if settings_row.smtp_enabled and settings_row.smtp_host and settings_row.smtp_from_address and settings_row.smtp_to_address:
        channels.append(
            SmtpNotifier(
                host=settings_row.smtp_host,
                port=settings_row.smtp_port or 587,
                username=settings_row.smtp_username,
                password=decrypt_secret(settings_row.smtp_password_encrypted)
                if settings_row.smtp_password_encrypted
                else None,
                from_address=settings_row.smtp_from_address,
                to_address=settings_row.smtp_to_address,
                use_tls=settings_row.smtp_use_tls,
            )
        )
    return channels


def _alert_subject(alert: Alert) -> str:
    return {
        "peer_offline": "VPN peer offline",
        "router_unreachable": "Concentrator unreachable",
        "login_failures": "Repeated failed logins",
    }.get(alert.type, alert.type)


async def notify_alert(db: AsyncSession, alert: Alert) -> None:
    settings_row = await get_or_create_settings(db)
    channels = await _build_channels(settings_row)
    if not channels:
        return
    subject = _alert_subject(alert)
    for channel in channels:
        try:
            await channel.send(subject, alert.message, alert.severity)
        except Exception as exc:  # noqa: BLE001 - a broken channel must never break alerting
            logger.error("Notification channel %s failed: %s", type(channel).__name__, exc)


async def send_test_telegram(bot_token: str, chat_id: str) -> tuple[bool, str]:
    """Send a test message and report real success/failure (unlike
    TelegramNotifier.send, which never raises so it can't break alerting)."""
    import httpx

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    text = "Test notification from Mikrotik VPN Monitor - if you see this, Telegram alerts are working."
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(url, json={"chat_id": chat_id, "text": text})
        if response.status_code >= 400:
            return False, f"Telegram API returned {response.status_code}: {response.text}"
        return True, "Test message sent."
    except httpx.HTTPError as exc:
        return False, str(exc)

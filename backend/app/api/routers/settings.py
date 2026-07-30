from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.crypto import decrypt_secret
from app.core.database import get_db
from app.core.deps import require_role
from app.models.notification_settings import NotificationSettings
from app.models.router_config import RouterConfig
from app.schemas.notification_settings import (
    NotificationSettingsOut,
    NotificationSettingsUpdate,
    TestNotificationResult,
    TestTelegramRequest,
)
from app.schemas.router_config import RouterConfigOut, RouterConfigUpdate, TestConnectionResult
from app.services import router_config_service
from app.services.mikrotik.exceptions import MikrotikError
from app.services.notifications import dispatcher

router = APIRouter(prefix="/settings", tags=["settings"], dependencies=[Depends(require_role("admin"))])


def _to_out(row: RouterConfig) -> RouterConfigOut:
    return RouterConfigOut.model_validate(row)


def _notification_settings_to_out(row: NotificationSettings) -> NotificationSettingsOut:
    return NotificationSettingsOut(
        telegram_enabled=row.telegram_enabled,
        telegram_chat_id=row.telegram_chat_id,
        telegram_token_configured=bool(row.telegram_bot_token_encrypted),
        smtp_enabled=row.smtp_enabled,
        smtp_host=row.smtp_host,
        smtp_port=row.smtp_port,
        smtp_username=row.smtp_username,
        smtp_password_configured=bool(row.smtp_password_encrypted),
        smtp_from_address=row.smtp_from_address,
        smtp_to_address=row.smtp_to_address,
        smtp_use_tls=row.smtp_use_tls,
        offline_threshold_minutes=row.offline_threshold_minutes,
        router_unreachable_realert_minutes=row.router_unreachable_realert_minutes,
        snapshot_retention_days=row.snapshot_retention_days,
        updated_at=row.updated_at,
    )


@router.get("/router", response_model=RouterConfigOut | None)
async def get_router_config(db: AsyncSession = Depends(get_db)) -> RouterConfigOut | None:
    row = await router_config_service.get_active_config(db)
    return _to_out(row) if row else None


@router.put("/router", response_model=RouterConfigOut)
async def update_router_config(
    body: RouterConfigUpdate, db: AsyncSession = Depends(get_db)
) -> RouterConfigOut:
    row = await router_config_service.upsert_config(db, body)
    return _to_out(row)


@router.post("/router/test-connection", response_model=TestConnectionResult)
async def test_router_connection(db: AsyncSession = Depends(get_db)) -> TestConnectionResult:
    client = await router_config_service.build_client(db)
    if client is None:
        return TestConnectionResult(success=False, message="Router is not configured yet.")
    try:
        await client.test_connection()
    except MikrotikError as exc:
        return TestConnectionResult(success=False, message=str(exc))
    return TestConnectionResult(success=True, message="Connection successful.")


@router.get("/notifications", response_model=NotificationSettingsOut)
async def get_notification_settings(db: AsyncSession = Depends(get_db)) -> NotificationSettingsOut:
    row = await dispatcher.get_or_create_settings(db)
    return _notification_settings_to_out(row)


@router.put("/notifications", response_model=NotificationSettingsOut)
async def update_notification_settings(
    body: NotificationSettingsUpdate, db: AsyncSession = Depends(get_db)
) -> NotificationSettingsOut:
    row = await dispatcher.update_settings(db, body)
    return _notification_settings_to_out(row)


@router.post("/notifications/test-telegram", response_model=TestNotificationResult)
async def test_telegram(body: TestTelegramRequest, db: AsyncSession = Depends(get_db)) -> TestNotificationResult:
    bot_token = body.bot_token
    chat_id = body.chat_id
    if not bot_token or not chat_id:
        row = await dispatcher.get_or_create_settings(db)
        if not bot_token:
            bot_token = decrypt_secret(row.telegram_bot_token_encrypted) if row.telegram_bot_token_encrypted else None
        if not chat_id:
            chat_id = row.telegram_chat_id
    if not bot_token or not chat_id:
        return TestNotificationResult(success=False, message="Telegram bot token and chat id are required.")

    success, message = await dispatcher.send_test_telegram(bot_token, chat_id)
    return TestNotificationResult(success=success, message=message)

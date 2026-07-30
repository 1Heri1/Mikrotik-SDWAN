import httpx

from app.core.logging import LOGGER_APP, get_logger

logger = get_logger(LOGGER_APP)

_SEVERITY_EMOJI = {"info": "ℹ️", "warning": "⚠️", "critical": "\U0001f6a8"}


class TelegramNotifier:
    def __init__(self, bot_token: str, chat_id: str):
        self._bot_token = bot_token
        self._chat_id = chat_id

    async def send(self, subject: str, message: str, severity: str = "info") -> None:
        emoji = _SEVERITY_EMOJI.get(severity, "")
        text = f"{emoji} *{subject}*\n{message}"
        url = f"https://api.telegram.org/bot{self._bot_token}/sendMessage"
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(
                    url, json={"chat_id": self._chat_id, "text": text, "parse_mode": "Markdown"}
                )
            if response.status_code >= 400:
                logger.error("Telegram notification failed (%s): %s", response.status_code, response.text)
        except httpx.HTTPError as exc:
            logger.error("Telegram notification failed: %s", exc)

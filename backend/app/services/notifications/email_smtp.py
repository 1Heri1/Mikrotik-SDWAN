from email.message import EmailMessage

import aiosmtplib

from app.core.logging import LOGGER_APP, get_logger

logger = get_logger(LOGGER_APP)


class SmtpNotifier:
    def __init__(
        self,
        host: str,
        port: int,
        username: str | None,
        password: str | None,
        from_address: str,
        to_address: str,
        use_tls: bool = True,
    ):
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._from_address = from_address
        self._to_address = to_address
        self._use_tls = use_tls

    async def send(self, subject: str, message: str, severity: str = "info") -> None:
        email = EmailMessage()
        email["Subject"] = f"[{severity.upper()}] {subject}"
        email["From"] = self._from_address
        email["To"] = self._to_address
        email.set_content(message)

        try:
            await aiosmtplib.send(
                email,
                hostname=self._host,
                port=self._port,
                username=self._username or None,
                password=self._password or None,
                start_tls=self._use_tls,
                timeout=10,
            )
        except (aiosmtplib.SMTPException, OSError) as exc:
            logger.error("SMTP notification failed: %s", exc)

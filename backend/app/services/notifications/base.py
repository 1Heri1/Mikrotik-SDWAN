from typing import Protocol


class NotificationChannel(Protocol):
    async def send(self, subject: str, message: str, severity: str) -> None:
        """Send a notification. Must never raise - implementations catch and
        log their own errors so a broken notification channel can never
        interrupt alert processing or the poll loop."""
        ...

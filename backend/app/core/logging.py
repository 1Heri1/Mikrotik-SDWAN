import logging
import os
from logging.handlers import RotatingFileHandler

from app.core.config import get_settings

_CONFIGURED = False

# Named loggers used across the app so operators can grep/filter by concern.
LOGGER_APP = "app"
LOGGER_SECURITY = "app.security"
LOGGER_AUDIT = "app.audit"
LOGGER_MIKROTIK = "app.mikrotik"
LOGGER_SCHEDULER = "app.scheduler"


def configure_logging() -> None:
    """Configure stdlib logging once at process startup.

    Writes to LOG_DIR/app.log with rotation (5 MB x 5 backups) and also
    emits to stdout/stderr so `docker logs` / `journalctl` capture output.
    """
    global _CONFIGURED
    if _CONFIGURED:
        return

    settings = get_settings()
    os.makedirs(settings.LOG_DIR, exist_ok=True)

    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)-8s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = RotatingFileHandler(
        os.path.join(settings.LOG_DIR, "app.log"),
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(logging.INFO if settings.ENV == "prod" else logging.DEBUG)
    root.addHandler(file_handler)
    root.addHandler(stream_handler)

    # Quiet noisy third-party loggers a bit.
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("apscheduler").setLevel(logging.WARNING)

    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)

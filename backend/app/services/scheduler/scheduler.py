from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.core.config import get_settings
from app.core.logging import LOGGER_SCHEDULER, get_logger
from app.services.scheduler.jobs import poll_job, prune_snapshots_job

logger = get_logger(LOGGER_SCHEDULER)


class SchedulerService:
    """Wraps a single in-process APScheduler instance.

    job_defaults=max_instances=1,coalesce=True ensures a slow or hanging poll
    can never queue up overlapping runs - if a poll is still running when the
    next interval fires, that run is simply skipped rather than piling up.
    """

    def __init__(self) -> None:
        self._scheduler = AsyncIOScheduler(
            job_defaults={"coalesce": True, "max_instances": 1, "misfire_grace_time": 30}
        )

    def start(self) -> None:
        settings = get_settings()
        self._scheduler.add_job(
            poll_job,
            "interval",
            seconds=settings.POLL_INTERVAL_SECONDS,
            id="poll_peers",
            replace_existing=True,
        )
        self._scheduler.add_job(
            prune_snapshots_job,
            "cron",
            hour=3,
            minute=0,
            id="prune_snapshots",
            replace_existing=True,
        )
        self._scheduler.start()
        logger.info("Scheduler started (poll interval=%ss)", settings.POLL_INTERVAL_SECONDS)

    def shutdown(self) -> None:
        self._scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")


scheduler_service = SchedulerService()

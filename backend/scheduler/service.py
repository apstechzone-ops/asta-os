from datetime import datetime
from typing import Any, Callable

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger

from backend.logging_ import get_logger
from backend.scheduler.interface import SchedulerInterface

logger = get_logger(__name__)


class SchedulerService(SchedulerInterface):
    name = "scheduler"

    def __init__(self) -> None:
        self._scheduler = AsyncIOScheduler()

    async def startup(self) -> None:
        self._scheduler.start()
        logger.info("Scheduler started")

    async def shutdown(self) -> None:
        self._scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")

    def health(self) -> dict:
        return {"module": self.name, "status": "ok" if self._scheduler.running else "stopped"}

    def schedule_once(self, job_id: str, run_at: datetime, fn: Callable, **kwargs: Any) -> None:
        self._scheduler.add_job(
            fn, trigger=DateTrigger(run_date=run_at), id=job_id, kwargs=kwargs, replace_existing=True
        )

    def schedule_cron(self, job_id: str, cron_expr: str, fn: Callable, **kwargs: Any) -> None:
        self._scheduler.add_job(
            fn,
            trigger=CronTrigger.from_crontab(cron_expr),
            id=job_id,
            kwargs=kwargs,
            replace_existing=True,
        )

    def cancel(self, job_id: str) -> None:
        self._scheduler.remove_job(job_id)

    def list_jobs(self) -> list[dict[str, Any]]:
        return [
            {"id": job.id, "next_run_time": str(job.next_run_time), "trigger": str(job.trigger)}
            for job in self._scheduler.get_jobs()
        ]


_scheduler_singleton: SchedulerService | None = None


def get_scheduler() -> SchedulerService:
    global _scheduler_singleton
    if _scheduler_singleton is None:
        _scheduler_singleton = SchedulerService()
    return _scheduler_singleton

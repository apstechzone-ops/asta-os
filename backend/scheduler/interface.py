from abc import abstractmethod
from datetime import datetime
from typing import Any, Callable

from backend.shared import ModuleBase


class SchedulerInterface(ModuleBase):
    """Contract for the Scheduler module: one-off and recurring jobs."""

    @abstractmethod
    def schedule_once(self, job_id: str, run_at: datetime, fn: Callable, **kwargs: Any) -> None:
        ...

    @abstractmethod
    def schedule_cron(self, job_id: str, cron_expr: str, fn: Callable, **kwargs: Any) -> None:
        ...

    @abstractmethod
    def cancel(self, job_id: str) -> None:
        ...

    @abstractmethod
    def list_jobs(self) -> list[dict[str, Any]]:
        ...

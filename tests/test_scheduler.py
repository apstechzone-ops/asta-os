from datetime import datetime, timedelta

import pytest

from backend.scheduler.service import SchedulerService


@pytest.mark.asyncio
async def test_schedule_once_and_cancel():
    scheduler = SchedulerService()
    await scheduler.startup()
    try:
        async def noop(message: str = "") -> None:
            pass

        scheduler.schedule_once("job-1", datetime.now() + timedelta(hours=1), noop, message="hi")
        jobs = scheduler.list_jobs()
        assert len(jobs) == 1
        assert jobs[0]["id"] == "job-1"

        scheduler.cancel("job-1")
        assert scheduler.list_jobs() == []
    finally:
        await scheduler.shutdown()


@pytest.mark.asyncio
async def test_schedule_cron():
    scheduler = SchedulerService()
    await scheduler.startup()
    try:
        async def noop(message: str = "") -> None:
            pass

        scheduler.schedule_cron("job-2", "0 9 * * *", noop, message="daily")
        jobs = scheduler.list_jobs()
        assert len(jobs) == 1
        assert jobs[0]["id"] == "job-2"
    finally:
        await scheduler.shutdown()

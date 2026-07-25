from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from backend.auth.dependencies import get_current_user
from backend.scheduler import get_scheduler
from backend.scheduler.jobs import log_reminder

router = APIRouter(prefix="/scheduler", tags=["scheduler"])


class ScheduleOnceRequest(BaseModel):
    job_id: str
    run_at: datetime
    message: str


class ScheduleCronRequest(BaseModel):
    job_id: str
    cron_expr: str  # e.g. "0 9 * * *" (every day at 9am)
    message: str


@router.get("/jobs")
async def list_jobs(_current_user: dict = Depends(get_current_user)):
    return get_scheduler().list_jobs()


@router.post("/jobs/once")
async def schedule_once(req: ScheduleOnceRequest, _current_user: dict = Depends(get_current_user)):
    get_scheduler().schedule_once(req.job_id, req.run_at, log_reminder, message=req.message)
    return {"status": "scheduled", "job_id": req.job_id}


@router.post("/jobs/cron")
async def schedule_cron(req: ScheduleCronRequest, _current_user: dict = Depends(get_current_user)):
    get_scheduler().schedule_cron(req.job_id, req.cron_expr, log_reminder, message=req.message)
    return {"status": "scheduled", "job_id": req.job_id}


@router.delete("/jobs/{job_id}")
async def cancel_job(job_id: str, _current_user: dict = Depends(get_current_user)):
    try:
        get_scheduler().cancel(job_id)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return {"status": "cancelled"}

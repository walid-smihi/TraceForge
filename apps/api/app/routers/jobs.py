import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from redis import Redis
from rq.command import send_stop_job_command
from rq.job import Job
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.schemas.job import JobResponse
from app.services import job_service
from app.services.project_service import get_project
from config import settings

router = APIRouter(tags=["jobs"])


def _redis() -> Redis:
    return Redis.from_url(settings.REDIS_URL)


@router.get("/projects/{project_id}/jobs", response_model=list[JobResponse])
async def list_jobs(project_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    project = await get_project(session, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return await job_service.list_jobs(session, project_id)


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    job = await job_service.get_job(session, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post("/jobs/{job_id}/cancel", response_model=JobResponse)
async def cancel_job(job_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    job = await job_service.get_job(session, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status not in ("pending", "running"):
        raise HTTPException(
            status_code=400, detail=f"Cannot cancel a job with status '{job.status}'"
        )

    conn = _redis()
    try:
        rq_job = Job.fetch(str(job_id), connection=conn)
        if rq_job.get_status().value in ("queued", "scheduled", "deferred"):
            rq_job.cancel()
        else:
            send_stop_job_command(conn, str(job_id))
    except Exception:
        pass

    job.status = "cancelled"
    job.completed_at = datetime.utcnow()
    await session.commit()
    await session.refresh(job)
    return job

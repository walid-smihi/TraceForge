import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.schemas.job import JobResponse
from app.services import job_service
from app.services.project_service import get_project

router = APIRouter(tags=["jobs"])


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

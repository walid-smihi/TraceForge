import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from redis import Redis
from rq import Queue
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.schemas.job import JobResponse
from app.schemas.requirement import RequirementCreate, RequirementResponse, RequirementUpdate
from app.services import job_service, requirement_service
from app.services.project_service import get_project
from config import settings

router = APIRouter(prefix="/projects/{project_id}/requirements", tags=["requirements"])


def _get_queue() -> Queue:
    return Queue("traceforge-jobs", connection=Redis.from_url(settings.REDIS_URL))


@router.get("", response_model=list[RequirementResponse])
async def list_requirements(
    project_id: uuid.UUID,
    req_type: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    is_ambiguous: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_session),
):
    project = await get_project(session, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return await requirement_service.list_requirements(
        session, project_id, req_type, priority, status_filter, is_ambiguous, search
    )


@router.post("", response_model=RequirementResponse, status_code=status.HTTP_201_CREATED)
async def create_requirement(
    project_id: uuid.UUID,
    data: RequirementCreate,
    session: AsyncSession = Depends(get_session),
):
    project = await get_project(session, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return await requirement_service.create_requirement(session, project_id, data)


@router.post("/extract", response_model=JobResponse, status_code=status.HTTP_202_ACCEPTED)
async def extract_requirements(
    project_id: uuid.UUID,
    document_id: uuid.UUID = Query(...),
    session: AsyncSession = Depends(get_session),
):
    project = await get_project(session, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    job = await job_service.create_job(
        session=session,
        project_id=project_id,
        job_type="extract_requirements",
        input_data={"document_id": str(document_id)},
    )
    _get_queue().enqueue(
        "app.workers.extract_requirements.run_extract_requirements",
        str(job.id),
        str(document_id),
        str(project_id),
        job_timeout=600,
    )
    return job


@router.get("/{req_id}", response_model=RequirementResponse)
async def get_requirement(
    project_id: uuid.UUID,
    req_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    req = await requirement_service.get_requirement(session, project_id, req_id)
    if not req:
        raise HTTPException(status_code=404, detail="Requirement not found")
    return req


@router.patch("/{req_id}", response_model=RequirementResponse)
async def update_requirement(
    project_id: uuid.UUID,
    req_id: uuid.UUID,
    data: RequirementUpdate,
    session: AsyncSession = Depends(get_session),
):
    req = await requirement_service.get_requirement(session, project_id, req_id)
    if not req:
        raise HTTPException(status_code=404, detail="Requirement not found")
    return await requirement_service.update_requirement(session, req, data)


@router.delete("/{req_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_requirement(
    project_id: uuid.UUID,
    req_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    req = await requirement_service.get_requirement(session, project_id, req_id)
    if not req:
        raise HTTPException(status_code=404, detail="Requirement not found")
    await requirement_service.delete_requirement(session, req)

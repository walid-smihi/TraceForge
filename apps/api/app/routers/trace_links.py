import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete as sa_delete
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.code_file import CodeFile
from app.models.requirement import Requirement
from app.models.trace_link import TraceLink
from app.schemas.job import JobResponse
from app.schemas.trace_link import TraceLinkResponse, TraceLinkUpdate
from app.services import job_service
from app.services.background import run_in_background
from app.services.project_service import get_project
from app.workers.generate_trace_links import _generate_trace_links

router = APIRouter(prefix="/projects/{project_id}/trace-links", tags=["trace-links"])

_VALID_STATUSES = {"suggested", "validated", "rejected", "needs_review"}


async def _enrich(session: AsyncSession, link: TraceLink) -> TraceLinkResponse:
    data = TraceLinkResponse.model_validate(link)
    if link.source_type == "requirement":
        req = await session.get(Requirement, link.source_id)
        if req:
            data.requirement_code = req.code
            data.requirement_title = req.title
    if link.target_type == "code_file":
        file = await session.get(CodeFile, link.target_id)
        if file:
            data.file_path = file.path
            data.file_language = file.language
            data.file_summary = file.summary
    return data


@router.post("/generate", response_model=JobResponse, status_code=status.HTTP_202_ACCEPTED)
async def generate_trace_links(
    project_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    project = await get_project(session, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    job = await job_service.create_job(
        session=session,
        project_id=project_id,
        job_type="suggest_links",
        input_data={},
    )

    run_in_background(str(job.id), _generate_trace_links(job.id, project_id))

    return job


@router.get("", response_model=list[TraceLinkResponse])
async def list_trace_links(
    project_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    project = await get_project(session, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    result = await session.execute(
        select(TraceLink)
        .where(TraceLink.project_id == project_id)
        .order_by(TraceLink.confidence_score.desc().nulls_last())
    )
    links = list(result.scalars().all())
    return [await _enrich(session, link) for link in links]


@router.patch("/{link_id}", response_model=TraceLinkResponse)
async def update_trace_link(
    project_id: uuid.UUID,
    link_id: uuid.UUID,
    data: TraceLinkUpdate,
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(TraceLink).where(
            TraceLink.id == link_id,
            TraceLink.project_id == project_id,
        )
    )
    link = result.scalar_one_or_none()
    if not link:
        raise HTTPException(status_code=404, detail="Trace link not found")

    if data.status not in _VALID_STATUSES:
        raise HTTPException(
            status_code=400, detail=f"Status must be one of: {', '.join(_VALID_STATUSES)}"
        )

    link.status = data.status
    if data.validation_note is not None:
        link.validation_note = data.validation_note
    await session.commit()
    await session.refresh(link)
    return await _enrich(session, link)


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def delete_all_trace_links(
    project_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    project = await get_project(session, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    await session.execute(sa_delete(TraceLink).where(TraceLink.project_id == project_id))
    await session.commit()


@router.delete("/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_trace_link(
    project_id: uuid.UUID,
    link_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(TraceLink).where(
            TraceLink.id == link_id,
            TraceLink.project_id == project_id,
        )
    )
    link = result.scalar_one_or_none()
    if not link:
        raise HTTPException(status_code=404, detail="Trace link not found")
    await session.delete(link)
    await session.commit()

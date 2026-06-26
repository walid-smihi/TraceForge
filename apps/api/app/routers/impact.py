import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.schemas.impact import ImpactAnalyzeRequest
from app.schemas.job import JobResponse
from app.services import job_service
from app.services.background import run_in_background
from app.services.project_service import get_project
from app.services.requirement_service import get_requirement
from app.workers.generate_impact_report import _generate_impact_report

router = APIRouter(prefix="/projects/{project_id}/impact", tags=["impact"])


@router.post("/analyze", response_model=JobResponse, status_code=status.HTTP_202_ACCEPTED)
async def analyze_impact(
    project_id: uuid.UUID,
    data: ImpactAnalyzeRequest,
    session: AsyncSession = Depends(get_session),
):
    project = await get_project(session, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    requirement = await get_requirement(session, project_id, data.requirement_id)
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")

    job = await job_service.create_job(
        session=session,
        project_id=project_id,
        job_type="generate_impact",
        input_data={
            "requirement_id": str(data.requirement_id),
            "modification_description": data.modification_description,
        },
    )

    run_in_background(
        str(job.id),
        _generate_impact_report(
            job.id, project_id, data.requirement_id, data.modification_description
        ),
    )

    return job

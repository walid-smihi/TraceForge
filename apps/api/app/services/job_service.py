import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analysis_job import AnalysisJob


async def create_job(
    session: AsyncSession,
    project_id: uuid.UUID,
    job_type: str,
    input_data: Optional[dict] = None,
) -> AnalysisJob:
    job = AnalysisJob(
        project_id=project_id,
        job_type=job_type,
        status="pending",
        progress=0,
        input_data=input_data,
    )
    session.add(job)
    await session.commit()
    await session.refresh(job)
    return job


async def get_job(session: AsyncSession, job_id: uuid.UUID) -> Optional[AnalysisJob]:
    return await session.get(AnalysisJob, job_id)


async def list_jobs(session: AsyncSession, project_id: uuid.UUID) -> list[AnalysisJob]:
    result = await session.execute(
        select(AnalysisJob)
        .where(AnalysisJob.project_id == project_id)
        .order_by(AnalysisJob.created_at.desc())
    )
    return list(result.scalars().all())

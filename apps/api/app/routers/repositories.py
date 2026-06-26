import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.schemas.job import JobResponse
from app.schemas.repository import CodeFileResponse, RepositoryCreate, RepositoryResponse
from app.services import job_service, repository_service
from app.services.background import run_in_background
from app.services.project_service import get_project
from app.workers.scan_repository import _scan_repository

router = APIRouter(prefix="/projects/{project_id}/repositories", tags=["repositories"])


@router.get("", response_model=list[RepositoryResponse])
async def list_repositories(
    project_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    project = await get_project(session, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return await repository_service.list_repositories(session, project_id)


@router.post("", response_model=JobResponse, status_code=status.HTTP_202_ACCEPTED)
async def add_repository(
    project_id: uuid.UUID,
    data: RepositoryCreate,
    session: AsyncSession = Depends(get_session),
):
    project = await get_project(session, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    repo = await repository_service.create_repository(session, project_id, data)

    job = await job_service.create_job(
        session=session,
        project_id=project_id,
        job_type="scan_repository",
        input_data={"repository_id": str(repo.id)},
    )

    run_in_background(str(job.id), _scan_repository(job.id, repo.id, project_id))

    return job


@router.get("/{repo_id}", response_model=RepositoryResponse)
async def get_repository(
    project_id: uuid.UUID,
    repo_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    repo = await repository_service.get_repository(session, project_id, repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    return repo


@router.get("/{repo_id}/files", response_model=list[CodeFileResponse])
async def list_files(
    project_id: uuid.UUID,
    repo_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    repo = await repository_service.get_repository(session, project_id, repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    return await repository_service.list_files(session, repo_id)


@router.delete("/{repo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_repository(
    project_id: uuid.UUID,
    repo_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    repo = await repository_service.get_repository(session, project_id, repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    await repository_service.delete_repository(session, repo)

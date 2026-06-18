import shutil
import uuid
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.code_file import CodeFile, CodeRepository
from app.schemas.repository import RepositoryCreate
from config import settings


async def create_repository(
    session: AsyncSession,
    project_id: uuid.UUID,
    data: RepositoryCreate,
) -> CodeRepository:
    if data.github_url:
        repo = CodeRepository(
            project_id=project_id,
            name=data.name,
            source_type="github",
            source_url=data.github_url,
            status="pending",
        )
    else:
        repo = CodeRepository(
            project_id=project_id,
            name=data.name,
            source_type="local",
            local_path=data.local_path,
            status="pending",
        )
    session.add(repo)
    await session.commit()
    await session.refresh(repo)
    return repo


async def get_repository(
    session: AsyncSession,
    project_id: uuid.UUID,
    repo_id: uuid.UUID,
) -> CodeRepository | None:
    result = await session.execute(
        select(CodeRepository).where(
            CodeRepository.id == repo_id,
            CodeRepository.project_id == project_id,
        )
    )
    return result.scalar_one_or_none()


async def list_repositories(
    session: AsyncSession,
    project_id: uuid.UUID,
) -> list[CodeRepository]:
    result = await session.execute(
        select(CodeRepository).where(CodeRepository.project_id == project_id)
    )
    return list(result.scalars().all())


async def list_files(
    session: AsyncSession,
    repository_id: uuid.UUID,
) -> list[CodeFile]:
    result = await session.execute(
        select(CodeFile).where(CodeFile.repository_id == repository_id).order_by(CodeFile.path)
    )
    return list(result.scalars().all())


async def delete_repository(session: AsyncSession, repo: CodeRepository) -> None:
    if repo.source_type == "github":
        clone_dir = Path(settings.STORAGE_PATH) / str(repo.project_id) / "repos" / str(repo.id)
        shutil.rmtree(clone_dir, ignore_errors=True)
    await session.delete(repo)
    await session.commit()

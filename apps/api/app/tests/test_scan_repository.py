import subprocess
import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.llm.base import LLMResponse
from app.models.code_file import CodeFile, CodeRepository
from app.services import job_service
from app.workers.scan_repository import _clone_github_repo, _scan_repository
from config import settings


class _StubLLM:
    def __init__(self, healthy: bool = True):
        self._healthy = healthy

    async def health_check(self) -> bool:
        return self._healthy

    async def complete(self, prompt: str, system: str = "", **kwargs) -> LLMResponse:
        content = '{"summary": "does stuff", "role": "service", "entities": ["Thing"]}'
        return LLMResponse(
            content=content, input_tokens=5, output_tokens=5, model="stub", provider="stub"
        )

    async def embed(self, text: str):
        raise NotImplementedError


@pytest.fixture
def local_git_repo(tmp_path):
    """A tiny local git repo we can clone via file:// — no network needed."""
    repo_dir = tmp_path / "source_repo"
    repo_dir.mkdir()
    (repo_dir / "main.py").write_text("print('hello')\n")
    subprocess.run(["git", "init", "-q", str(repo_dir)], check=True)
    subprocess.run(["git", "-C", str(repo_dir), "config", "user.email", "a@b.com"], check=True)
    subprocess.run(["git", "-C", str(repo_dir), "config", "user.name", "test"], check=True)
    subprocess.run(["git", "-C", str(repo_dir), "add", "."], check=True)
    subprocess.run(["git", "-C", str(repo_dir), "commit", "-q", "-m", "init"], check=True)
    return repo_dir


def test_clone_github_repo_success(local_git_repo, monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "STORAGE_PATH", str(tmp_path / "storage"))
    project_id = uuid.uuid4()
    repo_id = uuid.uuid4()

    dest = _clone_github_repo(f"file://{local_git_repo}", project_id, repo_id)

    assert dest.exists()
    assert (dest / "main.py").exists()


def test_clone_github_repo_invalid_url_raises(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "STORAGE_PATH", str(tmp_path / "storage"))
    project_id = uuid.uuid4()
    repo_id = uuid.uuid4()

    with pytest.raises(ValueError, match="git clone failed"):
        _clone_github_repo(f"file://{tmp_path}/does-not-exist", project_id, repo_id)


def test_clone_github_repo_overwrites_existing_dest(local_git_repo, monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "STORAGE_PATH", str(tmp_path / "storage"))
    project_id = uuid.uuid4()
    repo_id = uuid.uuid4()

    dest = _clone_github_repo(f"file://{local_git_repo}", project_id, repo_id)
    (dest / "stale_file.txt").write_text("should be gone after re-clone")

    dest2 = _clone_github_repo(f"file://{local_git_repo}", project_id, repo_id)

    assert dest == dest2
    assert not (dest2 / "stale_file.txt").exists()
    assert (dest2 / "main.py").exists()


@pytest.fixture
async def project_id(client: AsyncClient) -> str:
    resp = await client.post("/api/v1/projects", json={"name": "Scan Test Project"})
    return resp.json()["id"]


@pytest.mark.asyncio
async def test_missing_job_or_repo_returns_silently(session: AsyncSession):
    await _scan_repository(uuid.uuid4(), uuid.uuid4(), uuid.uuid4())


@pytest.mark.asyncio
async def test_scan_invalid_local_path_fails(session: AsyncSession, project_id: str):
    pid = uuid.UUID(project_id)
    repo = CodeRepository(
        project_id=pid, name="repo", source_type="local", local_path="/no/such/path"
    )
    session.add(repo)
    await session.flush()
    job = await job_service.create_job(session, pid, "scan_repository")
    await session.commit()

    with pytest.raises(ValueError):
        await _scan_repository(job.id, repo.id, pid)

    await session.refresh(job)
    await session.refresh(repo)
    assert job.status == "failed"
    assert repo.status == "failed"


@pytest.mark.asyncio
async def test_scan_empty_directory_completes_with_zero_files(
    session: AsyncSession, project_id: str, tmp_path
):
    pid = uuid.UUID(project_id)
    empty_dir = tmp_path / "empty_repo"
    empty_dir.mkdir()

    repo = CodeRepository(
        project_id=pid, name="repo", source_type="local", local_path=str(empty_dir)
    )
    session.add(repo)
    await session.flush()
    job = await job_service.create_job(session, pid, "scan_repository")
    await session.commit()

    await _scan_repository(job.id, repo.id, pid)

    await session.refresh(job)
    await session.refresh(repo)
    assert job.status == "completed"
    assert repo.status == "scanned"
    assert repo.file_count == 0


@pytest.mark.asyncio
async def test_scan_with_llm_summarizes_files(
    monkeypatch, session: AsyncSession, project_id: str, tmp_path
):
    pid = uuid.UUID(project_id)
    source = tmp_path / "myrepo"
    source.mkdir()
    (source / "main.py").write_text("\n".join(f"line_{i} = {i}" for i in range(20)) + "\n")
    (source / "test_main.py").write_text("def test_x():\n    assert True\n")

    repo = CodeRepository(project_id=pid, name="repo", source_type="local", local_path=str(source))
    session.add(repo)
    await session.flush()
    job = await job_service.create_job(session, pid, "scan_repository")
    await session.commit()

    monkeypatch.setattr("app.workers.scan_repository.get_provider", lambda: _StubLLM(healthy=True))

    await _scan_repository(job.id, repo.id, pid)

    await session.refresh(job)
    await session.refresh(repo)
    assert job.status == "completed"
    assert repo.file_count == 2
    assert repo.test_count == 1

    from sqlalchemy import select

    files_result = await session.execute(select(CodeFile).where(CodeFile.repository_id == repo.id))
    files = {f.path: f for f in files_result.scalars().all()}
    assert files["main.py"].summary == "does stuff"
    assert files["main.py"].role_detected == "service"
    assert files["test_main.py"].is_test_file is True


@pytest.mark.asyncio
async def test_scan_without_llm_skips_summaries(
    monkeypatch, session: AsyncSession, project_id: str, tmp_path
):
    pid = uuid.UUID(project_id)
    source = tmp_path / "myrepo2"
    source.mkdir()
    (source / "main.py").write_text("\n".join(f"line_{i} = {i}" for i in range(20)) + "\n")

    repo = CodeRepository(project_id=pid, name="repo", source_type="local", local_path=str(source))
    session.add(repo)
    await session.flush()
    job = await job_service.create_job(session, pid, "scan_repository")
    await session.commit()

    monkeypatch.setattr("app.workers.scan_repository.get_provider", lambda: _StubLLM(healthy=False))

    await _scan_repository(job.id, repo.id, pid)

    await session.refresh(job)
    assert job.status == "completed"

    from sqlalchemy import select

    files_result = await session.execute(select(CodeFile).where(CodeFile.repository_id == repo.id))
    files = list(files_result.scalars().all())
    assert files[0].summary is None


@pytest.mark.asyncio
async def test_scan_github_source_clones_then_scans(
    monkeypatch, local_git_repo, session: AsyncSession, project_id: str, tmp_path
):
    pid = uuid.UUID(project_id)
    monkeypatch.setattr(settings, "STORAGE_PATH", str(tmp_path / "storage"))

    repo = CodeRepository(
        project_id=pid,
        name="repo",
        source_type="github",
        source_url=f"file://{local_git_repo}",
    )
    session.add(repo)
    await session.flush()
    job = await job_service.create_job(session, pid, "scan_repository")
    await session.commit()

    monkeypatch.setattr("app.workers.scan_repository.get_provider", lambda: _StubLLM(healthy=False))

    await _scan_repository(job.id, repo.id, pid)

    await session.refresh(job)
    await session.refresh(repo)
    assert job.status == "completed"
    assert repo.status == "scanned"
    assert repo.file_count == 1

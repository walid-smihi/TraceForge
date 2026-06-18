import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.llm.base import LLMResponse
from app.models.code_file import CodeFile, CodeRepository
from app.models.requirement import Requirement
from app.models.trace_link import TraceLink
from app.services import job_service
from app.workers.generate_trace_links import _generate_trace_links


def _vec(seed: float) -> list[float]:
    return [seed] + [0.0] * 767


class _StubLLM:
    def __init__(self, healthy: bool = True, relevant: bool = True, embed_value: float = 1.0):
        self._healthy = healthy
        self._relevant = relevant
        self._embed_value = embed_value

    async def health_check(self) -> bool:
        return self._healthy

    async def embed(self, text: str) -> list[float]:
        return _vec(self._embed_value)

    async def complete(self, prompt: str, system: str = "", **kwargs) -> LLMResponse:
        verdict = '{"relevant": true, "confidence": 85, "justification": "matches"}'
        if not self._relevant:
            verdict = '{"relevant": false, "confidence": 10, "justification": "no match"}'
        return LLMResponse(
            content=verdict, input_tokens=5, output_tokens=5, model="stub", provider="stub"
        )


@pytest.fixture
async def project_id(client: AsyncClient) -> str:
    resp = await client.post("/api/v1/projects", json={"name": "Generate Links Test Project"})
    return resp.json()["id"]


@pytest.mark.asyncio
async def test_missing_job_returns_silently(session: AsyncSession):
    await _generate_trace_links(uuid.uuid4(), uuid.uuid4())


@pytest.mark.asyncio
async def test_fails_when_no_requirement_embeddings(session: AsyncSession, project_id: str):
    pid = uuid.UUID(project_id)
    job = await job_service.create_job(session, pid, "suggest_links")

    await _generate_trace_links(job.id, pid)

    await session.refresh(job)
    assert job.status == "failed"
    assert "exigence" in job.error_message.lower()


@pytest.mark.asyncio
async def test_fails_when_no_code_files(monkeypatch, session: AsyncSession, project_id: str):
    pid = uuid.UUID(project_id)
    req = Requirement(project_id=pid, code="REQ-001", title="Req", req_type="functional")
    session.add(req)
    await session.flush()
    req.embedding = _vec(1.0)
    await session.commit()

    job = await job_service.create_job(session, pid, "suggest_links")
    await _generate_trace_links(job.id, pid)

    await session.refresh(job)
    assert job.status == "failed"
    assert "fichier" in job.error_message.lower()


async def _seed_req_and_file(session: AsyncSession, project_id: str, file_embedding=None):
    pid = uuid.UUID(project_id)
    req = Requirement(project_id=pid, code="REQ-001", title="Req", req_type="functional")
    session.add(req)
    await session.flush()
    req.embedding = _vec(1.0)

    repo = CodeRepository(project_id=pid, name="repo", source_type="local")
    session.add(repo)
    await session.flush()

    code_file = CodeFile(
        repository_id=repo.id,
        project_id=pid,
        path="src/main.py",
        summary="does things",
        is_test_file=False,
    )
    session.add(code_file)
    await session.flush()
    code_file.embedding = file_embedding if file_embedding is not None else _vec(1.0)
    await session.commit()
    return req, code_file


@pytest.mark.asyncio
async def test_creates_links_with_llm_judging(monkeypatch, session: AsyncSession, project_id: str):
    pid = uuid.UUID(project_id)
    req, code_file = await _seed_req_and_file(session, project_id)

    job = await job_service.create_job(session, pid, "suggest_links")

    monkeypatch.setattr(
        "app.workers.generate_trace_links.get_provider", lambda: _StubLLM(relevant=True)
    )

    await _generate_trace_links(job.id, pid)

    await session.refresh(job)
    assert job.status == "completed"
    assert job.result_data["links_created"] == 1

    links_result = await session.execute(select(TraceLink).where(TraceLink.source_id == req.id))
    links = links_result.scalars().all()
    assert len(links) == 1


@pytest.mark.asyncio
async def test_no_links_when_llm_rejects_all_candidates(
    monkeypatch, session: AsyncSession, project_id: str
):
    pid = uuid.UUID(project_id)
    await _seed_req_and_file(session, project_id)
    job = await job_service.create_job(session, pid, "suggest_links")

    monkeypatch.setattr(
        "app.workers.generate_trace_links.get_provider", lambda: _StubLLM(relevant=False)
    )

    await _generate_trace_links(job.id, pid)

    await session.refresh(job)
    assert job.status == "completed"
    assert job.result_data["links_created"] == 0


@pytest.mark.asyncio
async def test_falls_back_to_cosine_when_llm_unavailable(
    monkeypatch, session: AsyncSession, project_id: str
):
    pid = uuid.UUID(project_id)
    await _seed_req_and_file(session, project_id)
    job = await job_service.create_job(session, pid, "suggest_links")

    monkeypatch.setattr(
        "app.workers.generate_trace_links.get_provider", lambda: _StubLLM(healthy=False)
    )

    await _generate_trace_links(job.id, pid)

    await session.refresh(job)
    assert job.status == "completed"
    assert job.result_data["links_created"] == 1


@pytest.mark.asyncio
async def test_computes_missing_file_embeddings(
    monkeypatch, session: AsyncSession, project_id: str
):
    pid = uuid.UUID(project_id)
    req, code_file = await _seed_req_and_file(session, project_id, file_embedding=None)
    code_file.embedding = None
    await session.commit()

    job = await job_service.create_job(session, pid, "suggest_links")
    monkeypatch.setattr(
        "app.workers.generate_trace_links.get_provider", lambda: _StubLLM(relevant=True)
    )

    await _generate_trace_links(job.id, pid)

    await session.refresh(job)
    assert job.status == "completed"
    assert job.result_data["files_indexed"] == 1

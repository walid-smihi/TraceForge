import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.llm.base import LLMResponse
from app.models.document import Document, DocumentChunk
from app.models.requirement import Requirement
from app.services import job_service
from app.workers.extract_requirements import _extract_requirements


class _StubLLM:
    def __init__(self, healthy: bool = True, content: str | None = None):
        self._healthy = healthy
        self._content = content or (
            '{"requirements": [{"title": "Do the thing", '
            '"description": "System must do the thing.", "type": "functional", '
            '"priority": "high", "is_ambiguous": false, "ambiguity_reason": null}]}'
        )

    async def health_check(self) -> bool:
        return self._healthy

    async def complete(self, prompt: str, system: str = "", **kwargs) -> LLMResponse:
        return LLMResponse(
            content=self._content, input_tokens=5, output_tokens=5, model="stub", provider="stub"
        )

    async def embed(self, text: str) -> list[float]:
        return [0.5] + [0.0] * 767


@pytest.fixture
async def project_id(client: AsyncClient) -> str:
    resp = await client.post("/api/v1/projects", json={"name": "Extract Req Worker Test"})
    return resp.json()["id"]


@pytest.fixture
async def document_with_chunk(session: AsyncSession, project_id: str):
    pid = uuid.UUID(project_id)
    document = Document(project_id=pid, name="spec.md", file_type="md", file_path="/tmp/x.md")
    session.add(document)
    await session.flush()
    chunk = DocumentChunk(document_id=document.id, chunk_index=0, content="REQ-001: do it.")
    session.add(chunk)
    await session.commit()
    return document


@pytest.mark.asyncio
async def test_missing_job_returns_silently(session: AsyncSession):
    await _extract_requirements(uuid.uuid4(), uuid.uuid4(), uuid.uuid4())


@pytest.mark.asyncio
async def test_fails_when_no_chunks(session: AsyncSession, project_id: str):
    pid = uuid.UUID(project_id)
    document = Document(project_id=pid, name="empty.md", file_type="md", file_path="/tmp/y.md")
    session.add(document)
    await session.flush()
    job = await job_service.create_job(session, pid, "extract_requirements")
    await session.commit()

    await _extract_requirements(job.id, document.id, pid)

    await session.refresh(job)
    assert job.status == "failed"
    assert "chunk" in job.error_message.lower()


@pytest.mark.asyncio
async def test_extract_requirements_success(
    monkeypatch, session: AsyncSession, project_id: str, document_with_chunk
):
    pid = uuid.UUID(project_id)
    job = await job_service.create_job(session, pid, "extract_requirements")
    await session.commit()

    monkeypatch.setattr("app.workers.extract_requirements.get_provider", lambda: _StubLLM())

    await _extract_requirements(job.id, document_with_chunk.id, pid)

    await session.refresh(job)
    assert job.status == "completed"
    assert job.result_data["requirements_created"] == 1

    reqs_result = await session.execute(select(Requirement).where(Requirement.project_id == pid))
    reqs = list(reqs_result.scalars().all())
    assert len(reqs) == 1
    assert reqs[0].title == "Do the thing"
    assert reqs[0].embedding is not None


@pytest.mark.asyncio
async def test_extract_requirements_dedups_existing_titles(
    monkeypatch, session: AsyncSession, project_id: str, document_with_chunk
):
    pid = uuid.UUID(project_id)
    existing = Requirement(
        project_id=pid, code="REQ-001", title="Do the thing", req_type="functional"
    )
    session.add(existing)
    await session.commit()

    job = await job_service.create_job(session, pid, "extract_requirements")
    await session.commit()

    monkeypatch.setattr("app.workers.extract_requirements.get_provider", lambda: _StubLLM())

    await _extract_requirements(job.id, document_with_chunk.id, pid)

    await session.refresh(job)
    assert job.result_data["requirements_created"] == 0

    reqs_result = await session.execute(select(Requirement).where(Requirement.project_id == pid))
    assert len(list(reqs_result.scalars().all())) == 1


@pytest.mark.asyncio
async def test_extract_requirements_skips_chunk_on_bad_json(
    monkeypatch, session: AsyncSession, project_id: str, document_with_chunk
):
    pid = uuid.UUID(project_id)
    job = await job_service.create_job(session, pid, "extract_requirements")
    await session.commit()

    monkeypatch.setattr(
        "app.workers.extract_requirements.get_provider",
        lambda: _StubLLM(content="not json at all"),
    )

    await _extract_requirements(job.id, document_with_chunk.id, pid)

    await session.refresh(job)
    assert job.status == "completed"
    assert job.result_data["requirements_created"] == 0


@pytest.mark.asyncio
async def test_extract_requirements_falls_back_to_mock_when_llm_unavailable(
    monkeypatch, session: AsyncSession, project_id: str, document_with_chunk
):
    pid = uuid.UUID(project_id)
    job = await job_service.create_job(session, pid, "extract_requirements")
    await session.commit()

    monkeypatch.setattr(
        "app.workers.extract_requirements.get_provider",
        lambda: _StubLLM(healthy=False),
    )

    await _extract_requirements(job.id, document_with_chunk.id, pid)

    await session.refresh(job)
    assert job.status == "completed"
    # MockProvider returns its own fixed set of requirements regardless of input.
    assert job.result_data["requirements_created"] > 0

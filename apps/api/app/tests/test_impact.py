import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.code_file import CodeFile, CodeRepository
from app.models.requirement import Requirement
from app.models.trace_link import TraceLink
from app.services import job_service
from app.services.impact_service import build_impact_report
from app.workers.generate_impact_report import _generate_impact_report


class _StubLLM:
    def __init__(self, summary: str = "Résumé de test", healthy: bool = True):
        self._summary = summary
        self._healthy = healthy

    async def health_check(self) -> bool:
        return self._healthy

    async def complete(self, prompt: str, system: str = "", **kwargs):
        from app.llm.base import LLMResponse

        return LLMResponse(
            content=f'{{"summary": "{self._summary}"}}',
            input_tokens=10,
            output_tokens=10,
            model="stub",
            provider="stub",
        )

    async def embed(self, text: str):
        raise NotImplementedError


@pytest.fixture
async def project_id(client: AsyncClient) -> str:
    resp = await client.post("/api/v1/projects", json={"name": "Impact Test Project"})
    return resp.json()["id"]


@pytest.mark.asyncio
async def test_analyze_impact_requirement_not_found(client: AsyncClient, project_id: str):
    resp = await client.post(
        f"/api/v1/projects/{project_id}/impact/analyze",
        json={
            "requirement_id": "00000000-0000-0000-0000-000000000000",
            "modification_description": "test",
        },
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_analyze_impact_creates_job(client: AsyncClient, project_id: str):
    req_resp = await client.post(
        f"/api/v1/projects/{project_id}/requirements",
        json={"title": "Some requirement", "req_type": "functional"},
    )
    req_id = req_resp.json()["id"]

    resp = await client.post(
        f"/api/v1/projects/{project_id}/impact/analyze",
        json={"requirement_id": req_id, "modification_description": "Add a field"},
    )
    assert resp.status_code == 202
    assert resp.json()["job_type"] == "generate_impact"
    assert resp.json()["status"] == "pending"


@pytest.mark.asyncio
async def test_build_impact_report_direct_and_indirect(session: AsyncSession, project_id: str):
    pid = uuid.UUID(project_id)

    req_a = Requirement(project_id=pid, code="REQ-A", title="Req A", req_type="functional")
    req_b = Requirement(project_id=pid, code="REQ-B", title="Req B", req_type="functional")
    session.add_all([req_a, req_b])
    await session.flush()

    repo = CodeRepository(project_id=pid, name="repo", source_type="local")
    session.add(repo)
    await session.flush()

    shared_file = CodeFile(
        repository_id=repo.id, project_id=pid, path="src/shared.py", is_test_file=False
    )
    test_file = CodeFile(
        repository_id=repo.id, project_id=pid, path="src/test_shared.py", is_test_file=True
    )
    session.add_all([shared_file, test_file])
    await session.flush()

    session.add_all(
        [
            TraceLink(
                project_id=pid,
                source_type="requirement",
                source_id=req_a.id,
                target_type="code_file",
                target_id=shared_file.id,
                status="suggested",
            ),
            TraceLink(
                project_id=pid,
                source_type="requirement",
                source_id=req_a.id,
                target_type="code_file",
                target_id=test_file.id,
                status="validated",
            ),
            TraceLink(
                project_id=pid,
                source_type="requirement",
                source_id=req_b.id,
                target_type="code_file",
                target_id=shared_file.id,
                status="suggested",
            ),
        ]
    )
    await session.commit()

    report = await build_impact_report(session, pid, req_a.id)

    assert report["requirement"]["code"] == "REQ-A"
    assert [f["path"] for f in report["direct_files"]] == ["src/shared.py"]
    assert [f["path"] for f in report["direct_tests"]] == ["src/test_shared.py"]
    assert [r["code"] for r in report["indirect_requirements"]] == ["REQ-B"]


@pytest.mark.asyncio
async def test_build_impact_report_unknown_requirement_raises(
    session: AsyncSession, project_id: str
):
    with pytest.raises(ValueError):
        await build_impact_report(
            session, uuid.UUID(project_id), uuid.UUID("00000000-0000-0000-0000-000000000000")
        )


@pytest.mark.asyncio
async def test_generate_impact_report_worker_success(
    monkeypatch, session: AsyncSession, project_id: str
):
    pid = uuid.UUID(project_id)
    req = Requirement(project_id=pid, code="REQ-001", title="Req", req_type="functional")
    session.add(req)
    await session.commit()

    job = await job_service.create_job(session, pid, "generate_impact")

    monkeypatch.setattr("app.workers.generate_impact_report.get_provider", lambda: _StubLLM())

    await _generate_impact_report(job.id, pid, req.id, "Add a field")

    await session.refresh(job)
    assert job.status == "completed"
    assert job.progress == 100
    assert job.result_data["summary"] == "Résumé de test"
    assert job.result_data["requirement"]["code"] == "REQ-001"


@pytest.mark.asyncio
async def test_generate_impact_report_worker_llm_unavailable(
    monkeypatch, session: AsyncSession, project_id: str
):
    pid = uuid.UUID(project_id)
    req = Requirement(project_id=pid, code="REQ-001", title="Req", req_type="functional")
    session.add(req)
    await session.commit()

    job = await job_service.create_job(session, pid, "generate_impact")

    monkeypatch.setattr(
        "app.workers.generate_impact_report.get_provider",
        lambda: _StubLLM(healthy=False),
    )

    await _generate_impact_report(job.id, pid, req.id, "Add a field")

    await session.refresh(job)
    assert job.status == "completed"
    assert job.result_data["summary"] is None


@pytest.mark.asyncio
async def test_generate_impact_report_worker_unknown_requirement_fails(
    session: AsyncSession, project_id: str
):
    pid = uuid.UUID(project_id)
    job = await job_service.create_job(session, pid, "generate_impact")

    with pytest.raises(ValueError):
        await _generate_impact_report(job.id, pid, uuid.uuid4(), "Add a field")

    await session.refresh(job)
    assert job.status == "failed"
    assert job.error_message is not None


@pytest.mark.asyncio
async def test_generate_impact_report_worker_missing_job_returns(session: AsyncSession):
    # Should return silently without raising when the job doesn't exist.
    await _generate_impact_report(uuid.uuid4(), uuid.uuid4(), uuid.uuid4(), "x")

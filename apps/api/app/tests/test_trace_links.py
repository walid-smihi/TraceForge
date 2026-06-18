import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.code_file import CodeFile, CodeRepository
from app.models.requirement import Requirement
from app.models.trace_link import TraceLink

_UNKNOWN_PROJECT = "00000000-0000-0000-0000-000000000000"


@pytest.fixture
async def project_id(client: AsyncClient) -> str:
    resp = await client.post("/api/v1/projects", json={"name": "Trace Link Test Project"})
    return resp.json()["id"]


@pytest.fixture
async def seeded_link(session: AsyncSession, project_id: str):
    pid = uuid.UUID(project_id)
    req = Requirement(project_id=pid, code="REQ-001", title="Req", req_type="functional")
    session.add(req)
    await session.flush()

    repo = CodeRepository(project_id=pid, name="repo", source_type="local")
    session.add(repo)
    await session.flush()

    code_file = CodeFile(
        repository_id=repo.id,
        project_id=pid,
        path="src/main.py",
        language="Python",
        summary="Entry point",
    )
    session.add(code_file)
    await session.flush()

    link = TraceLink(
        project_id=pid,
        source_type="requirement",
        source_id=req.id,
        target_type="code_file",
        target_id=code_file.id,
        status="suggested",
        confidence_score=0.8,
    )
    session.add(link)
    await session.commit()
    await session.refresh(link)
    return link, req, code_file


@pytest.mark.asyncio
async def test_list_trace_links_empty(client: AsyncClient, project_id: str):
    resp = await client.get(f"/api/v1/projects/{project_id}/trace-links")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_delete_all_trace_links(client: AsyncClient, project_id: str):
    resp = await client.delete(f"/api/v1/projects/{project_id}/trace-links")
    assert resp.status_code == 204

    resp = await client.get(f"/api/v1/projects/{project_id}/trace-links")
    assert resp.json() == []


@pytest.mark.asyncio
async def test_delete_all_trace_links_unknown_project(client: AsyncClient):
    resp = await client.delete("/api/v1/projects/00000000-0000-0000-0000-000000000000/trace-links")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_unknown_trace_link(client: AsyncClient, project_id: str):
    resp = await client.patch(
        f"/api/v1/projects/{project_id}/trace-links/00000000-0000-0000-0000-000000000000",
        json={"status": "validated"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_trace_links_unknown_project(client: AsyncClient):
    resp = await client.get(f"/api/v1/projects/{_UNKNOWN_PROJECT}/trace-links")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_generate_trace_links_unknown_project(client: AsyncClient):
    resp = await client.post(f"/api/v1/projects/{_UNKNOWN_PROJECT}/trace-links/generate")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_generate_trace_links_enqueues_job(client: AsyncClient, project_id: str):
    resp = await client.post(f"/api/v1/projects/{project_id}/trace-links/generate")
    assert resp.status_code == 202
    assert resp.json()["job_type"] == "suggest_links"


@pytest.mark.asyncio
async def test_list_trace_links_enriched(client: AsyncClient, project_id: str, seeded_link):
    _, req, code_file = seeded_link
    resp = await client.get(f"/api/v1/projects/{project_id}/trace-links")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["requirement_code"] == req.code
    assert data[0]["requirement_title"] == req.title
    assert data[0]["file_path"] == code_file.path
    assert data[0]["file_language"] == code_file.language
    assert data[0]["file_summary"] == code_file.summary


@pytest.mark.asyncio
async def test_update_trace_link_status(client: AsyncClient, project_id: str, seeded_link):
    link, _, _ = seeded_link
    resp = await client.patch(
        f"/api/v1/projects/{project_id}/trace-links/{link.id}",
        json={"status": "validated"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "validated"


@pytest.mark.asyncio
async def test_update_trace_link_invalid_status(client: AsyncClient, project_id: str, seeded_link):
    link, _, _ = seeded_link
    resp = await client.patch(
        f"/api/v1/projects/{project_id}/trace-links/{link.id}",
        json={"status": "not-a-status"},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_delete_single_trace_link(client: AsyncClient, project_id: str, seeded_link):
    link, _, _ = seeded_link
    resp = await client.delete(f"/api/v1/projects/{project_id}/trace-links/{link.id}")
    assert resp.status_code == 204

    resp = await client.get(f"/api/v1/projects/{project_id}/trace-links")
    assert resp.json() == []


@pytest.mark.asyncio
async def test_delete_single_trace_link_not_found(client: AsyncClient, project_id: str):
    resp = await client.delete(
        f"/api/v1/projects/{project_id}/trace-links/00000000-0000-0000-0000-000000000000"
    )
    assert resp.status_code == 404

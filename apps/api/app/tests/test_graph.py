import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.code_file import CodeFile, CodeRepository
from app.models.conflict import DetectedConflict
from app.models.requirement import Requirement
from app.models.trace_link import TraceLink
from app.services.graph_service import build_graph, get_metrics


@pytest.fixture
async def project_id(client: AsyncClient) -> str:
    resp = await client.post("/api/v1/projects", json={"name": "Graph Test Project"})
    return resp.json()["id"]


async def _seed_linked_graph(session: AsyncSession, project_id: str):
    pid = uuid.UUID(project_id)
    req = Requirement(
        project_id=pid, code="REQ-001", title="Req", req_type="functional", priority="critical"
    )
    session.add(req)
    await session.flush()

    repo = CodeRepository(project_id=pid, name="repo", source_type="local")
    session.add(repo)
    await session.flush()

    code_file = CodeFile(
        repository_id=repo.id, project_id=pid, path="src/main.py", is_test_file=False
    )
    test_file = CodeFile(
        repository_id=repo.id, project_id=pid, path="src/test_main.py", is_test_file=True
    )
    session.add_all([code_file, test_file])
    await session.flush()

    link = TraceLink(
        project_id=pid,
        source_type="requirement",
        source_id=req.id,
        target_type="code_file",
        target_id=code_file.id,
        status="validated",
        confidence_score=0.9,
    )
    session.add(link)

    conflict = DetectedConflict(
        project_id=pid,
        rule_id="RULE-001",
        severity="critical",
        title="open conflict",
        status="open",
    )
    session.add(conflict)
    await session.commit()
    return req, code_file, test_file


@pytest.mark.asyncio
async def test_graph_empty(client: AsyncClient, project_id: str):
    resp = await client.get(f"/api/v1/projects/{project_id}/graph")
    assert resp.status_code == 200
    data = resp.json()
    assert data["nodes"] == []
    assert data["edges"] == []


@pytest.mark.asyncio
async def test_graph_includes_requirement_node(client: AsyncClient, project_id: str):
    await client.post(
        f"/api/v1/projects/{project_id}/requirements",
        json={"title": "User can login", "req_type": "functional"},
    )
    resp = await client.get(f"/api/v1/projects/{project_id}/graph")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["nodes"]) == 1
    assert data["nodes"][0]["node_type"] == "requirement"
    assert data["nodes"][0]["data"]["is_linked"] is False


@pytest.mark.asyncio
async def test_metrics_empty_project(client: AsyncClient, project_id: str):
    resp = await client.get(f"/api/v1/projects/{project_id}/metrics")
    assert resp.status_code == 200
    data = resp.json()
    assert data["requirements_total"] == 0
    assert data["coverage_percent"] == 0.0


@pytest.mark.asyncio
async def test_metrics_counts_unlinked_requirement(client: AsyncClient, project_id: str):
    await client.post(
        f"/api/v1/projects/{project_id}/requirements",
        json={"title": "User can login", "req_type": "functional"},
    )
    resp = await client.get(f"/api/v1/projects/{project_id}/metrics")
    assert resp.status_code == 200
    data = resp.json()
    assert data["requirements_total"] == 1
    assert data["requirements_unlinked"] == 1
    assert data["coverage_percent"] == 0.0


@pytest.mark.asyncio
async def test_graph_not_found_for_unknown_project(client: AsyncClient):
    resp = await client.get("/api/v1/projects/00000000-0000-0000-0000-000000000000/graph")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_graph_includes_files_and_edges(
    session: AsyncSession, client: AsyncClient, project_id: str
):
    req, code_file, test_file = await _seed_linked_graph(session, project_id)

    resp = await client.get(f"/api/v1/projects/{project_id}/graph")
    assert resp.status_code == 200
    data = resp.json()

    node_ids = {n["id"] for n in data["nodes"]}
    assert f"requirement:{req.id}" in node_ids
    assert f"code_file:{code_file.id}" in node_ids
    assert f"code_file:{test_file.id}" in node_ids

    req_node = next(n for n in data["nodes"] if n["id"] == f"requirement:{req.id}")
    assert req_node["data"]["is_linked"] is True

    file_node = next(n for n in data["nodes"] if n["id"] == f"code_file:{code_file.id}")
    assert file_node["data"]["is_linked"] is True

    test_node = next(n for n in data["nodes"] if n["id"] == f"code_file:{test_file.id}")
    assert test_node["data"]["is_test_file"] is True
    assert test_node["data"]["is_linked"] is False

    assert len(data["edges"]) == 1
    edge = data["edges"][0]
    assert edge["source"] == f"requirement:{req.id}"
    assert edge["target"] == f"code_file:{code_file.id}"
    assert edge["status"] == "validated"
    assert edge["confidence_score"] == 0.9


@pytest.mark.asyncio
async def test_metrics_with_links_files_and_conflicts(
    session: AsyncSession, client: AsyncClient, project_id: str
):
    await _seed_linked_graph(session, project_id)

    resp = await client.get(f"/api/v1/projects/{project_id}/metrics")
    assert resp.status_code == 200
    data = resp.json()

    assert data["requirements_total"] == 1
    assert data["requirements_linked"] == 1
    assert data["requirements_unlinked"] == 0
    assert data["coverage_percent"] == 100.0
    assert data["code_files_total"] == 2
    assert data["code_files_linked"] == 1
    assert data["test_files_total"] == 1
    assert data["links_total"] == 1
    assert data["links_validated"] == 1
    assert data["conflicts_open"] == 1


@pytest.mark.asyncio
async def test_build_graph_direct_call(session: AsyncSession, project_id: str):
    req, code_file, test_file = await _seed_linked_graph(session, project_id)

    result = await build_graph(session, uuid.UUID(project_id))

    node_ids = {n.id for n in result.nodes}
    assert f"requirement:{req.id}" in node_ids
    assert f"code_file:{code_file.id}" in node_ids
    assert f"code_file:{test_file.id}" in node_ids
    assert len(result.edges) == 1


@pytest.mark.asyncio
async def test_get_metrics_direct_call(session: AsyncSession, project_id: str):
    await _seed_linked_graph(session, project_id)

    metrics = await get_metrics(session, uuid.UUID(project_id))

    assert metrics.requirements_total == 1
    assert metrics.coverage_percent == 100.0
    assert metrics.conflicts_open == 1

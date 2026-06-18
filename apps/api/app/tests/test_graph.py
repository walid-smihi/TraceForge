import pytest
from httpx import AsyncClient


@pytest.fixture
async def project_id(client: AsyncClient) -> str:
    resp = await client.post("/api/v1/projects", json={"name": "Graph Test Project"})
    return resp.json()["id"]


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

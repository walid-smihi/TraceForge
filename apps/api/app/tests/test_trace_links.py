import pytest
from httpx import AsyncClient


@pytest.fixture
async def project_id(client: AsyncClient) -> str:
    resp = await client.post("/api/v1/projects", json={"name": "Trace Link Test Project"})
    return resp.json()["id"]


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

import pytest
from httpx import AsyncClient


@pytest.fixture
async def project_id(client: AsyncClient) -> str:
    resp = await client.post("/api/v1/projects", json={"name": "Req Test Project"})
    return resp.json()["id"]


@pytest.mark.asyncio
async def test_list_requirements_empty(client: AsyncClient, project_id: str):
    resp = await client.get(f"/api/v1/projects/{project_id}/requirements")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_create_requirement(client: AsyncClient, project_id: str):
    resp = await client.post(
        f"/api/v1/projects/{project_id}/requirements",
        json={
            "title": "User can login",
            "description": "The user must be able to login.",
            "req_type": "functional",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["code"] == "REQ-001"
    assert data["title"] == "User can login"
    assert data["is_ambiguous"] is False


@pytest.mark.asyncio
async def test_auto_increment_codes(client: AsyncClient, project_id: str):
    await client.post(f"/api/v1/projects/{project_id}/requirements", json={"title": "First"})
    resp = await client.post(
        f"/api/v1/projects/{project_id}/requirements", json={"title": "Second"}
    )
    assert resp.json()["code"] == "REQ-002"


@pytest.mark.asyncio
async def test_ambiguity_detection(client: AsyncClient, project_id: str):
    resp = await client.post(
        f"/api/v1/projects/{project_id}/requirements",
        json={"title": "The system must be fast and reliable", "req_type": "performance"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["is_ambiguous"] is True
    assert data["ambiguity_reason"] is not None


@pytest.mark.asyncio
async def test_filter_by_type(client: AsyncClient, project_id: str):
    await client.post(
        f"/api/v1/projects/{project_id}/requirements",
        json={"title": "Func req", "req_type": "functional"},
    )
    await client.post(
        f"/api/v1/projects/{project_id}/requirements",
        json={"title": "Security req", "req_type": "security"},
    )
    resp = await client.get(f"/api/v1/projects/{project_id}/requirements?req_type=security")
    assert len(resp.json()) == 1
    assert resp.json()[0]["req_type"] == "security"


@pytest.mark.asyncio
async def test_update_requirement(client: AsyncClient, project_id: str):
    create = await client.post(
        f"/api/v1/projects/{project_id}/requirements", json={"title": "Original"}
    )
    req_id = create.json()["id"]
    resp = await client.patch(
        f"/api/v1/projects/{project_id}/requirements/{req_id}", json={"title": "Updated"}
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "Updated"
    assert resp.json()["status"] == "modified"


@pytest.mark.asyncio
async def test_delete_requirement(client: AsyncClient, project_id: str):
    create = await client.post(
        f"/api/v1/projects/{project_id}/requirements", json={"title": "To delete"}
    )
    req_id = create.json()["id"]
    resp = await client.delete(f"/api/v1/projects/{project_id}/requirements/{req_id}")
    assert resp.status_code == 204

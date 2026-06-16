import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_projects_empty(client: AsyncClient):
    response = await client.get("/api/v1/projects")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_create_project(client: AsyncClient):
    response = await client.post(
        "/api/v1/projects",
        json={"name": "Test Project", "description": "A test", "domain": "finance"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Project"
    assert data["description"] == "A test"
    assert "id" in data


@pytest.mark.asyncio
async def test_get_project(client: AsyncClient):
    create = await client.post("/api/v1/projects", json={"name": "Get Test"})
    project_id = create.json()["id"]

    response = await client.get(f"/api/v1/projects/{project_id}")
    assert response.status_code == 200
    assert response.json()["id"] == project_id


@pytest.mark.asyncio
async def test_get_project_not_found(client: AsyncClient):
    response = await client.get("/api/v1/projects/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_project(client: AsyncClient):
    create = await client.post("/api/v1/projects", json={"name": "Update Test"})
    project_id = create.json()["id"]

    response = await client.patch(
        f"/api/v1/projects/{project_id}", json={"name": "Updated Name"}
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Name"


@pytest.mark.asyncio
async def test_delete_project(client: AsyncClient):
    create = await client.post("/api/v1/projects", json={"name": "Delete Test"})
    project_id = create.json()["id"]

    response = await client.delete(f"/api/v1/projects/{project_id}")
    assert response.status_code == 204

    get = await client.get(f"/api/v1/projects/{project_id}")
    assert get.status_code == 404

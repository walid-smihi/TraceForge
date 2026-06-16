import io

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_upload_document_invalid_type(client: AsyncClient):
    create = await client.post("/api/v1/projects", json={"name": "Doc Test Project"})
    project_id = create.json()["id"]

    response = await client.post(
        f"/api/v1/projects/{project_id}/documents",
        files={"file": ("test.exe", b"MZ\x90\x00", "application/octet-stream")},
    )
    assert response.status_code == 415


@pytest.mark.asyncio
async def test_list_documents_empty(client: AsyncClient):
    create = await client.post("/api/v1/projects", json={"name": "Docs Empty Test"})
    project_id = create.json()["id"]

    response = await client.get(f"/api/v1/projects/{project_id}/documents")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_upload_markdown_document(client: AsyncClient):
    create = await client.post("/api/v1/projects", json={"name": "MD Upload Test"})
    project_id = create.json()["id"]

    md_content = b"# Spec\n\nREQ-001: The system shall process payments.\n"
    response = await client.post(
        f"/api/v1/projects/{project_id}/documents",
        files={"file": ("spec.md", io.BytesIO(md_content), "text/markdown")},
    )
    assert response.status_code == 202
    data = response.json()
    assert data["job_type"] == "extract_document"
    assert data["status"] == "pending"


@pytest.mark.asyncio
async def test_get_document_not_found(client: AsyncClient):
    create = await client.post("/api/v1/projects", json={"name": "Doc 404 Test"})
    project_id = create.json()["id"]

    response = await client.get(
        f"/api/v1/projects/{project_id}/documents/00000000-0000-0000-0000-000000000000"
    )
    assert response.status_code == 404

import pytest
from httpx import AsyncClient


@pytest.fixture
async def project_id(client: AsyncClient) -> str:
    resp = await client.post("/api/v1/projects", json={"name": "Repository Test Project"})
    return resp.json()["id"]


@pytest.mark.asyncio
async def test_add_local_repository(client: AsyncClient, project_id: str):
    resp = await client.post(
        f"/api/v1/projects/{project_id}/repositories",
        json={"name": "local repo", "local_path": "/tmp/some-repo"},
    )
    assert resp.status_code == 202
    assert resp.json()["job_type"] == "scan_repository"

    repos = await client.get(f"/api/v1/projects/{project_id}/repositories")
    repo = repos.json()[0]
    assert repo["source_type"] == "local"
    assert repo["local_path"] == "/tmp/some-repo"


@pytest.mark.asyncio
async def test_add_github_repository(client: AsyncClient, project_id: str):
    resp = await client.post(
        f"/api/v1/projects/{project_id}/repositories",
        json={"name": "github repo", "github_url": "https://github.com/octocat/Hello-World"},
    )
    assert resp.status_code == 202

    repos = await client.get(f"/api/v1/projects/{project_id}/repositories")
    repo = repos.json()[0]
    assert repo["source_type"] == "github"
    assert repo["source_url"] == "https://github.com/octocat/Hello-World"
    assert repo["local_path"] is None


@pytest.mark.asyncio
async def test_add_repository_rejects_both_sources(client: AsyncClient, project_id: str):
    resp = await client.post(
        f"/api/v1/projects/{project_id}/repositories",
        json={
            "name": "ambiguous",
            "local_path": "/tmp/x",
            "github_url": "https://github.com/octocat/Hello-World",
        },
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_add_repository_rejects_no_source(client: AsyncClient, project_id: str):
    resp = await client.post(
        f"/api/v1/projects/{project_id}/repositories",
        json={"name": "no source"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_add_repository_rejects_malformed_github_url(client: AsyncClient, project_id: str):
    resp = await client.post(
        f"/api/v1/projects/{project_id}/repositories",
        json={"name": "bad url", "github_url": "not-a-github-url"},
    )
    assert resp.status_code == 422

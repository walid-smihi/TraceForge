import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.code_file import CodeFile, CodeRepository
from app.models.requirement import Requirement


class _StubProvider:
    """Returns a fixed embedding per query so cosine similarity is deterministic."""

    def __init__(self, query_embedding: list[float]):
        self._query_embedding = query_embedding

    async def embed(self, text: str) -> list[float]:
        return self._query_embedding

    async def health_check(self) -> bool:
        return True

    async def complete(self, prompt: str, system: str = "", **kwargs):
        raise NotImplementedError


@pytest.fixture
async def project_id(client: AsyncClient) -> str:
    resp = await client.post("/api/v1/projects", json={"name": "Search Test Project"})
    return resp.json()["id"]


@pytest.mark.asyncio
async def test_search_requires_query_param(client: AsyncClient, project_id: str):
    resp = await client.get(f"/api/v1/projects/{project_id}/search")
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_search_project_not_found(client: AsyncClient):
    resp = await client.get("/api/v1/projects/00000000-0000-0000-0000-000000000000/search?q=test")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_semantic_search_ranks_by_similarity(
    monkeypatch, session: AsyncSession, client: AsyncClient, project_id: str
):
    pid = uuid.UUID(project_id)

    close_match = [1.0, 0.0, 0.0] + [0.0] * 765
    far_match = [0.0, 1.0, 0.0] + [0.0] * 765

    req_close = Requirement(
        project_id=pid, code="REQ-001", title="Close match", req_type="functional"
    )
    req_far = Requirement(project_id=pid, code="REQ-002", title="Far match", req_type="functional")
    session.add_all([req_close, req_far])
    await session.flush()
    req_close.embedding = close_match
    req_far.embedding = far_match
    await session.commit()

    monkeypatch.setattr(
        "app.services.search_service.get_provider",
        lambda: _StubProvider(close_match),
    )

    resp = await client.get(f"/api/v1/projects/{project_id}/search?q=anything")
    assert resp.status_code == 200
    results = resp.json()

    assert len(results) == 1
    assert results[0]["code"] == "REQ-001"
    assert results[0]["score"] == 1.0


@pytest.mark.asyncio
async def test_semantic_search_target_filter(
    monkeypatch, session: AsyncSession, client: AsyncClient, project_id: str
):
    pid = uuid.UUID(project_id)
    vec = [1.0] + [0.0] * 767

    req = Requirement(project_id=pid, code="REQ-001", title="Req", req_type="functional")
    session.add(req)
    await session.flush()
    req.embedding = vec

    repo = CodeRepository(project_id=pid, name="repo", source_type="local")
    session.add(repo)
    await session.flush()

    code_file = CodeFile(repository_id=repo.id, project_id=pid, path="src/main.py")
    session.add(code_file)
    await session.flush()
    code_file.embedding = vec
    await session.commit()

    monkeypatch.setattr("app.services.search_service.get_provider", lambda: _StubProvider(vec))

    resp = await client.get(f"/api/v1/projects/{project_id}/search?q=x&target=code_file")
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) == 1
    assert results[0]["type"] == "code_file"
    assert results[0]["code"] == "src/main.py"


@pytest.mark.asyncio
async def test_semantic_search_llm_unavailable(monkeypatch, client: AsyncClient, project_id: str):
    class _DownProvider:
        async def health_check(self) -> bool:
            return False

    monkeypatch.setattr("app.services.search_service.get_provider", lambda: _DownProvider())

    resp = await client.get(f"/api/v1/projects/{project_id}/search?q=test")
    assert resp.status_code == 503

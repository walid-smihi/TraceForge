import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.conflict_service import detect_conflicts


@pytest.fixture
async def project_id(client: AsyncClient) -> str:
    resp = await client.post("/api/v1/projects", json={"name": "Conflict Test Project"})
    return resp.json()["id"]


@pytest.mark.asyncio
async def test_list_conflicts_empty(client: AsyncClient, project_id: str):
    resp = await client.get(f"/api/v1/projects/{project_id}/conflicts")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_detect_rule_001_critical_requirement_without_test(
    client: AsyncClient, project_id: str
):
    await client.post(
        f"/api/v1/projects/{project_id}/requirements",
        json={"title": "Critical thing", "req_type": "functional", "priority": "critical"},
    )

    resp = await client.post(f"/api/v1/projects/{project_id}/conflicts/detect")
    assert resp.status_code == 200
    conflicts = resp.json()
    assert any(c["rule_id"] == "RULE-001" for c in conflicts)


@pytest.mark.asyncio
async def test_detect_rule_006_security_requirement_without_test(
    client: AsyncClient, project_id: str
):
    await client.post(
        f"/api/v1/projects/{project_id}/requirements",
        json={"title": "Secure thing", "req_type": "security", "priority": "low"},
    )

    resp = await client.post(f"/api/v1/projects/{project_id}/conflicts/detect")
    assert resp.status_code == 200
    conflicts = resp.json()
    assert any(c["rule_id"] == "RULE-006" for c in conflicts)


@pytest.mark.asyncio
async def test_detect_rule_002_numeric_temporal_conflict(session: AsyncSession, project_id: str):
    import uuid

    from app.models.requirement import Requirement

    req_a = Requirement(
        project_id=uuid.UUID(project_id),
        code="REQ-100",
        title="Réservation stock",
        description="La réservation de stock doit expirer après 4 minutes maximum.",
        req_type="functional",
    )
    req_b = Requirement(
        project_id=uuid.UUID(project_id),
        code="REQ-101",
        title="Validation paiement",
        description="La validation du paiement et de la réservation peut prendre jusqu'à 5 minutes.",
        req_type="functional",
    )
    session.add_all([req_a, req_b])
    await session.commit()

    count = await detect_conflicts(session, uuid.UUID(project_id))
    assert count >= 1


@pytest.mark.asyncio
async def test_update_conflict_status(client: AsyncClient, project_id: str):
    await client.post(
        f"/api/v1/projects/{project_id}/requirements",
        json={"title": "Critical thing", "req_type": "functional", "priority": "critical"},
    )
    detect_resp = await client.post(f"/api/v1/projects/{project_id}/conflicts/detect")
    conflict_id = detect_resp.json()[0]["id"]

    resp = await client.patch(
        f"/api/v1/projects/{project_id}/conflicts/{conflict_id}",
        json={"status": "resolved"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "resolved"
    assert resp.json()["resolved_at"] is not None


@pytest.mark.asyncio
async def test_update_conflict_invalid_status(client: AsyncClient, project_id: str):
    await client.post(
        f"/api/v1/projects/{project_id}/requirements",
        json={"title": "Critical thing", "req_type": "functional", "priority": "critical"},
    )
    detect_resp = await client.post(f"/api/v1/projects/{project_id}/conflicts/detect")
    conflict_id = detect_resp.json()[0]["id"]

    resp = await client.patch(
        f"/api/v1/projects/{project_id}/conflicts/{conflict_id}",
        json={"status": "not-a-status"},
    )
    assert resp.status_code == 400

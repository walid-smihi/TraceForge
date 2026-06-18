import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analysis_job import AnalysisJob

SAMPLE_REPORT = {
    "requirement": {
        "id": "00000000-0000-0000-0000-000000000001",
        "code": "REQ-001",
        "title": "Create project",
        "description": "Users can create a project.",
    },
    "modification_description": "Add a tags field",
    "summary": "This change touches the project model and schema.",
    "direct_files": [{"path": "app/models/project.py", "language": "Python", "summary": "Model"}],
    "direct_tests": [],
    "indirect_requirements": [{"code": "REQ-002", "title": "List projects"}],
    "conflicts": [{"rule_id": "RULE-001", "title": "REQ-001 sans test", "description": "..."}],
}


@pytest.fixture
async def project_id(client: AsyncClient) -> str:
    resp = await client.post("/api/v1/projects", json={"name": "Export Test Project"})
    return resp.json()["id"]


@pytest.fixture
async def completed_impact_job(session: AsyncSession, project_id: str) -> str:
    job = AnalysisJob(
        project_id=uuid.UUID(project_id),
        job_type="generate_impact",
        status="completed",
        progress=100,
        result_data=SAMPLE_REPORT,
    )
    session.add(job)
    await session.commit()
    await session.refresh(job)
    return str(job.id)


@pytest.mark.asyncio
async def test_export_impact_not_found(client: AsyncClient, project_id: str):
    resp = await client.get(
        f"/api/v1/projects/{project_id}/export/impact/00000000-0000-0000-0000-000000000000"
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_export_impact_not_ready(session: AsyncSession, client: AsyncClient, project_id: str):
    job = AnalysisJob(
        project_id=uuid.UUID(project_id),
        job_type="generate_impact",
        status="running",
        progress=50,
    )
    session.add(job)
    await session.commit()
    await session.refresh(job)

    resp = await client.get(f"/api/v1/projects/{project_id}/export/impact/{job.id}")
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_export_impact_markdown(
    client: AsyncClient, project_id: str, completed_impact_job: str
):
    resp = await client.get(
        f"/api/v1/projects/{project_id}/export/impact/{completed_impact_job}?format=md"
    )
    assert resp.status_code == 200
    assert "text/markdown" in resp.headers["content-type"]
    assert "REQ-001" in resp.text
    assert "app/models/project.py" in resp.text


@pytest.mark.asyncio
async def test_export_impact_pdf(client: AsyncClient, project_id: str, completed_impact_job: str):
    resp = await client.get(
        f"/api/v1/projects/{project_id}/export/impact/{completed_impact_job}?format=pdf"
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"
    assert resp.content.startswith(b"%PDF")

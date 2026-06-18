import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document, DocumentChunk
from app.services import job_service
from app.workers.extract_document import _extract_document


@pytest.fixture
async def project_id(client: AsyncClient) -> str:
    resp = await client.post("/api/v1/projects", json={"name": "Extract Document Test"})
    return resp.json()["id"]


@pytest.mark.asyncio
async def test_missing_job_or_document_returns_silently(session: AsyncSession):
    await _extract_document(uuid.uuid4(), uuid.uuid4())


@pytest.mark.asyncio
async def test_extract_document_success(session: AsyncSession, project_id: str, tmp_path):
    pid = uuid.UUID(project_id)
    md_file = tmp_path / "spec.md"
    md_file.write_text("# Title\n\nREQ-001: do the thing.\n\nREQ-002: do another thing.\n")

    document = Document(project_id=pid, name="spec.md", file_type="md", file_path=str(md_file))
    session.add(document)
    await session.flush()
    job = await job_service.create_job(session, pid, "extract_document")
    await session.commit()

    await _extract_document(job.id, document.id)

    await session.refresh(job)
    await session.refresh(document)
    assert job.status == "completed"
    assert job.progress == 100
    assert document.status == "processed"
    assert job.result_data["chunks_count"] >= 1

    chunks_result = await session.execute(
        select(DocumentChunk).where(DocumentChunk.document_id == document.id)
    )
    chunks = list(chunks_result.scalars().all())
    assert len(chunks) == job.result_data["chunks_count"]


@pytest.mark.asyncio
async def test_extract_document_replaces_existing_chunks(
    session: AsyncSession, project_id: str, tmp_path
):
    pid = uuid.UUID(project_id)
    md_file = tmp_path / "spec2.md"
    md_file.write_text("REQ-001: short text.\n")

    document = Document(project_id=pid, name="spec2.md", file_type="md", file_path=str(md_file))
    session.add(document)
    await session.flush()
    job = await job_service.create_job(session, pid, "extract_document")
    await session.commit()

    await _extract_document(job.id, document.id)
    await session.refresh(job)
    first_count = job.result_data["chunks_count"]

    job2 = await job_service.create_job(session, pid, "extract_document")
    await session.commit()
    await _extract_document(job2.id, document.id)

    chunks_result = await session.execute(
        select(DocumentChunk).where(DocumentChunk.document_id == document.id)
    )
    chunks = list(chunks_result.scalars().all())
    assert len(chunks) == first_count


@pytest.mark.asyncio
async def test_extract_document_failure_marks_job_and_document_failed(
    session: AsyncSession, project_id: str
):
    pid = uuid.UUID(project_id)
    document = Document(
        project_id=pid,
        name="missing.md",
        file_type="md",
        file_path="/no/such/file.md",
    )
    session.add(document)
    await session.flush()
    job = await job_service.create_job(session, pid, "extract_document")
    await session.commit()

    with pytest.raises(Exception):
        await _extract_document(job.id, document.id)

    await session.refresh(job)
    await session.refresh(document)
    assert job.status == "failed"
    assert document.status == "error"
    assert document.error_message is not None

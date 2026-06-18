import uuid
from pathlib import Path

import magic
from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from redis import Redis
from rq import Queue
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.schemas.document import DocumentChunkResponse, DocumentResponse
from app.schemas.job import JobResponse
from app.services import document_service, job_service
from app.services.project_service import get_project
from config import settings

router = APIRouter(prefix="/projects/{project_id}/documents", tags=["documents"])


def _get_queue() -> Queue:
    redis = Redis.from_url(settings.REDIS_URL)
    return Queue("traceforge-jobs", connection=redis)


def _save_file(project_id: uuid.UUID, file: UploadFile, content: bytes) -> tuple[str, str]:
    ext = Path(file.filename or "file").suffix.lstrip(".").lower() or "bin"
    storage_dir = Path(settings.STORAGE_PATH) / str(project_id)
    storage_dir.mkdir(parents=True, exist_ok=True)
    file_path = storage_dir / f"{uuid.uuid4()}.{ext}"
    file_path.write_bytes(content)
    return str(file_path), ext


@router.get("", response_model=list[DocumentResponse])
async def list_documents(project_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    project = await get_project(session, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return await document_service.list_documents(session, project_id)


@router.post("", response_model=JobResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    project_id: uuid.UUID,
    file: UploadFile,
    session: AsyncSession = Depends(get_session),
):
    project = await get_project(session, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    content = await file.read()
    size_mb = len(content) / (1024 * 1024)
    if size_mb > settings.MAX_UPLOAD_SIZE_MB:
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({size_mb:.1f}MB > {settings.MAX_UPLOAD_SIZE_MB}MB)",
        )

    mime = magic.from_buffer(content[:2048], mime=True)
    if mime not in document_service.ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=415, detail=f"Unsupported file type: {mime}")

    file_path, ext = _save_file(project_id, file, content)

    if ext not in document_service.ALLOWED_EXTENSIONS:
        Path(file_path).unlink(missing_ok=True)
        raise HTTPException(status_code=415, detail=f"Unsupported extension: {ext}")

    document = await document_service.create_document(
        session=session,
        project_id=project_id,
        name=file.filename or "document",
        file_type=ext,
        file_path=file_path,
        file_size_bytes=len(content),
    )

    job = await job_service.create_job(
        session=session,
        project_id=project_id,
        job_type="extract_document",
        input_data={"document_id": str(document.id)},
    )

    queue = _get_queue()
    queue.enqueue(
        "app.workers.extract_document.run_extract_document",
        str(job.id),
        str(document.id),
        job_timeout=120,
    )

    return job


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    project_id: uuid.UUID,
    document_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    doc = await document_service.get_document(session, project_id, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.get("/{document_id}/chunks", response_model=list[DocumentChunkResponse])
async def list_chunks(
    project_id: uuid.UUID,
    document_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    doc = await document_service.get_document(session, project_id, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return await document_service.list_chunks(session, document_id)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    project_id: uuid.UUID,
    document_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    doc = await document_service.get_document(session, project_id, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    await document_service.delete_document(session, doc)

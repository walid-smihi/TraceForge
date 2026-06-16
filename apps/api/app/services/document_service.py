import uuid
from pathlib import Path
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document, DocumentChunk


ALLOWED_EXTENSIONS = {"pdf", "docx", "md", "txt"}
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/markdown",
    "text/plain",
    "text/x-markdown",
}


async def list_documents(session: AsyncSession, project_id: uuid.UUID) -> list[Document]:
    result = await session.execute(
        select(Document)
        .where(Document.project_id == project_id)
        .order_by(Document.created_at.desc())
    )
    return list(result.scalars().all())


async def get_document(
    session: AsyncSession, project_id: uuid.UUID, document_id: uuid.UUID
) -> Optional[Document]:
    result = await session.execute(
        select(Document).where(
            Document.id == document_id, Document.project_id == project_id
        )
    )
    return result.scalar_one_or_none()


async def create_document(
    session: AsyncSession,
    project_id: uuid.UUID,
    name: str,
    file_type: str,
    file_path: str,
    file_size_bytes: int,
) -> Document:
    doc = Document(
        project_id=project_id,
        name=name,
        file_type=file_type,
        file_path=file_path,
        file_size_bytes=file_size_bytes,
        status="uploaded",
    )
    session.add(doc)
    await session.commit()
    await session.refresh(doc)
    return doc


async def delete_document(session: AsyncSession, document: Document) -> None:
    path = Path(document.file_path)
    if path.exists():
        path.unlink()
    await session.delete(document)
    await session.commit()


async def list_chunks(
    session: AsyncSession, document_id: uuid.UUID
) -> list[DocumentChunk]:
    result = await session.execute(
        select(DocumentChunk)
        .where(DocumentChunk.document_id == document_id)
        .order_by(DocumentChunk.chunk_index)
    )
    return list(result.scalars().all())

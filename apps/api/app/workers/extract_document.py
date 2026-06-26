import uuid
from datetime import datetime

from sqlalchemy import select

from app.database import async_session_factory
from app.llm.mock_provider import MockProvider
from app.models.analysis_job import AnalysisJob
from app.models.document import Document, DocumentChunk
from app.parsers.text_extractor import chunk_text, extract_text


async def _extract_document(job_id: uuid.UUID, document_id: uuid.UUID) -> None:
    async with async_session_factory() as session:
        job = await session.get(AnalysisJob, job_id)
        document = await session.get(Document, document_id)

        if not job or not document:
            return

        job.status = "running"
        job.started_at = datetime.utcnow()
        job.progress = 0
        await session.commit()

        try:
            text = extract_text(document.file_path, document.file_type)
            job.progress = 40
            await session.commit()

            raw_chunks = chunk_text(text)
            job.progress = 60
            await session.commit()

            existing = await session.execute(
                select(DocumentChunk).where(DocumentChunk.document_id == document_id)
            )
            for chunk in existing.scalars().all():
                await session.delete(chunk)

            for i, chunk_data in enumerate(raw_chunks):
                chunk = DocumentChunk(
                    document_id=document_id,
                    chunk_index=i,
                    content=chunk_data["content"],
                    section_title=chunk_data.get("section_title"),
                )
                session.add(chunk)

            job.progress = 80
            await session.commit()

            llm = MockProvider()
            req_result = await llm.complete(
                prompt=f"Extract requirements from:\n\n{text[:3000]}",
                system="You are a requirements analyst.",
            )

            document.status = "processed"
            job.status = "completed"
            job.progress = 100
            job.completed_at = datetime.utcnow()
            job.result_data = {
                "chunks_count": len(raw_chunks),
                "requirements_preview": req_result.content,
            }
            await session.commit()

        except Exception as exc:
            job.status = "failed"
            job.error_message = str(exc)
            job.completed_at = datetime.utcnow()
            document.status = "error"
            document.error_message = str(exc)
            await session.commit()
            raise

import asyncio
import json
import logging
import uuid
from datetime import datetime

from sqlalchemy import select

from app.database import async_session_factory
from app.llm.provider_factory import get_provider
from app.models.analysis_job import AnalysisJob
from app.models.document import DocumentChunk
from app.models.requirement import Requirement
from app.schemas.requirement import RequirementCreate
from app.services.requirement_service import create_requirement
from app.llm.prompts import EXTRACT_REQUIREMENTS_PROMPT, EXTRACT_REQUIREMENTS_SYSTEM

logger = logging.getLogger(__name__)


def run_extract_requirements(job_id: str, document_id: str, project_id: str) -> None:
    asyncio.run(_extract_requirements(
        uuid.UUID(job_id), uuid.UUID(document_id), uuid.UUID(project_id)
    ))


async def _extract_requirements(
    job_id: uuid.UUID, document_id: uuid.UUID, project_id: uuid.UUID
) -> None:
    async with async_session_factory() as session:
        job = await session.get(AnalysisJob, job_id)
        if not job:
            return

        job.status = "running"
        job.started_at = datetime.utcnow()
        job.progress = 0
        await session.commit()

        try:
            result = await session.execute(
                select(DocumentChunk)
                .where(DocumentChunk.document_id == document_id)
                .order_by(DocumentChunk.chunk_index)
            )
            chunks = result.scalars().all()

            if not chunks:
                job.status = "failed"
                job.error_message = "No chunks found — run document extraction first"
                job.completed_at = datetime.utcnow()
                await session.commit()
                return

            full_text = "\n\n".join(c.content for c in chunks)
            job.progress = 20
            await session.commit()

            llm = get_provider()
            available = await llm.health_check()
            if not available:
                logger.warning("LLM provider unavailable, falling back to MockProvider")
                from app.llm.mock_provider import MockProvider
                llm = MockProvider()

            prompt = EXTRACT_REQUIREMENTS_PROMPT.format(document_text=full_text[:8000])
            response = await llm.complete(prompt, system=EXTRACT_REQUIREMENTS_SYSTEM)
            job.progress = 60
            await session.commit()

            try:
                data = json.loads(response.content)
                raw_reqs = data.get("requirements", [])
            except json.JSONDecodeError:
                raw_reqs = []
                logger.error("LLM returned invalid JSON: %s", response.content[:200])

            existing = await session.execute(
                select(Requirement).where(Requirement.project_id == project_id)
            )
            existing_titles = {r.title.lower() for r in existing.scalars().all()}

            created = 0
            for raw in raw_reqs:
                title = raw.get("title", "").strip()
                if not title or title.lower() in existing_titles:
                    continue
                existing_titles.add(title.lower())

                data_create = RequirementCreate(
                    title=title,
                    description=raw.get("description"),
                    req_type=raw.get("type", "functional"),
                    priority=raw.get("priority", "medium"),
                    is_ambiguous=raw.get("is_ambiguous", False),
                    ambiguity_reason=raw.get("ambiguity_reason"),
                )
                await create_requirement(session, project_id, data_create, document_id)
                created += 1

            job.progress = 90
            await session.commit()

            # Generate embeddings for each requirement
            reqs_result = await session.execute(
                select(Requirement)
                .where(Requirement.project_id == project_id, Requirement.embedding.is_(None))
            )
            for req in reqs_result.scalars().all():
                try:
                    embedding = await llm.embed(f"{req.title} {req.description or ''}")
                    req.embedding = embedding
                except Exception:
                    pass
            await session.commit()

            job.status = "completed"
            job.progress = 100
            job.completed_at = datetime.utcnow()
            job.result_data = {"requirements_created": created}
            await session.commit()

        except Exception as exc:
            logger.exception("extract_requirements failed")
            job.status = "failed"
            job.error_message = str(exc)
            job.completed_at = datetime.utcnow()
            await session.commit()
            raise

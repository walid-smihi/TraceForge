import asyncio
import json
import logging
import uuid
from datetime import datetime

from sqlalchemy import select

from app.database import async_session_factory
from app.llm.prompts import EXTRACT_REQUIREMENTS_PROMPT, EXTRACT_REQUIREMENTS_SYSTEM
from app.llm.provider_factory import get_provider
from app.models.analysis_job import AnalysisJob
from app.models.document import DocumentChunk
from app.models.requirement import Requirement
from app.schemas.requirement import RequirementCreate
from app.services.requirement_service import create_requirement

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
            chunks = list(result.scalars().all())

            if not chunks:
                job.status = "failed"
                job.error_message = "No chunks found — run document extraction first"
                job.completed_at = datetime.utcnow()
                await session.commit()
                return

            llm = get_provider()
            available = await llm.health_check()
            if not available:
                logger.warning("LLM unavailable, falling back to MockProvider")
                from app.llm.mock_provider import MockProvider
                llm = MockProvider()

            existing = await session.execute(
                select(Requirement).where(Requirement.project_id == project_id)
            )
            seen_titles = {r.title.lower() for r in existing.scalars().all()}
            created = 0

            for i, chunk in enumerate(chunks):
                progress = 10 + int((i / len(chunks)) * 70)
                job.progress = progress
                await session.commit()

                prompt = EXTRACT_REQUIREMENTS_PROMPT.format(
                    document_text=chunk.content[:2000]
                )
                try:
                    response = await asyncio.wait_for(
                        llm.complete(prompt, system=EXTRACT_REQUIREMENTS_SYSTEM),
                        timeout=90.0,
                    )
                    raw_content = response.content.strip()
                    # Fix truncated JSON by closing unclosed structures
                    if raw_content and not raw_content.endswith("}"):
                        raw_content = raw_content.rsplit(",", 1)[0] + "]}"
                    data = json.loads(raw_content)
                    raw_reqs = data.get("requirements", [])
                except asyncio.TimeoutError:
                    logger.warning("Chunk %d timed out after 90s, skipping", i)
                    continue
                except (json.JSONDecodeError, Exception) as e:
                    logger.warning("Chunk %d error: %s", i, e)
                    continue

                for raw in raw_reqs:
                    title = raw.get("title", "").strip()
                    if not title or title.lower() in seen_titles:
                        continue
                    seen_titles.add(title.lower())
                    await create_requirement(
                        session, project_id,
                        RequirementCreate(
                            title=title,
                            description=raw.get("description"),
                            req_type=raw.get("type", "functional"),
                            priority=raw.get("priority", "medium"),
                            is_ambiguous=raw.get("is_ambiguous", False),
                            ambiguity_reason=raw.get("ambiguity_reason"),
                        ),
                        document_id,
                    )
                    created += 1

            job.progress = 85
            await session.commit()

            reqs_result = await session.execute(
                select(Requirement).where(
                    Requirement.project_id == project_id,
                    Requirement.embedding.is_(None),
                )
            )
            for req in reqs_result.scalars().all():
                try:
                    req.embedding = await llm.embed(f"{req.title} {req.description or ''}")
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

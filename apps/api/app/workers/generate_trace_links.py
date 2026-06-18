import asyncio
import logging
import math
import uuid
from datetime import datetime

from sqlalchemy import delete, select

from app.database import async_session_factory
from app.llm.provider_factory import get_provider
from app.models.analysis_job import AnalysisJob
from app.models.code_file import CodeFile
from app.models.requirement import Requirement
from app.models.trace_link import TraceLink

logger = logging.getLogger(__name__)

TOP_K = 5
MIN_SCORE = 0.40


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def run_generate_trace_links(job_id: str, project_id: str) -> None:
    asyncio.run(_generate_trace_links(uuid.UUID(job_id), uuid.UUID(project_id)))


async def _generate_trace_links(job_id: uuid.UUID, project_id: uuid.UUID) -> None:
    async with async_session_factory() as session:
        job = await session.get(AnalysisJob, job_id)
        if not job:
            return

        job.status = "running"
        job.started_at = datetime.utcnow()
        job.progress = 5
        await session.commit()

        try:
            reqs_result = await session.execute(
                select(Requirement).where(
                    Requirement.project_id == project_id,
                    Requirement.embedding.is_not(None),
                )
            )
            reqs = list(reqs_result.scalars().all())

            if not reqs:
                job.status = "failed"
                job.error_message = "Aucune exigence avec embedding. Relancez l'extraction d'abord."
                job.completed_at = datetime.utcnow()
                await session.commit()
                return

            job.progress = 15
            await session.commit()

            files_result = await session.execute(
                select(CodeFile).where(
                    CodeFile.project_id == project_id,
                    CodeFile.is_test_file == False,  # noqa: E712
                )
            )
            files = list(files_result.scalars().all())

            if not files:
                job.status = "failed"
                job.error_message = "Aucun fichier de code. Scannez un dépôt d'abord."
                job.completed_at = datetime.utcnow()
                await session.commit()
                return

            job.progress = 20
            await session.commit()

            # Compute embeddings for files that don't have one
            llm = get_provider()
            llm_ok = await llm.health_check()
            files_without_emb = [f for f in files if f.embedding is None]

            if files_without_emb and llm_ok:
                for i, f in enumerate(files_without_emb):
                    text = f.path
                    if f.summary:
                        text += " " + f.summary
                    if f.entities:
                        text += " " + " ".join(f.entities)
                    try:
                        f.embedding = await llm.embed(text)
                    except Exception as e:
                        logger.warning("Embed failed for %s: %s", f.path, e)
                    if i % 10 == 0:
                        await session.commit()
                await session.commit()

            job.progress = 40
            await session.commit()

            # Remove old auto-suggested links
            await session.execute(
                delete(TraceLink).where(
                    TraceLink.project_id == project_id,
                    TraceLink.status == "suggested",
                    TraceLink.is_manual == False,  # noqa: E712
                )
            )
            await session.commit()

            job.progress = 45
            await session.commit()

            files_with_emb = [f for f in files if f.embedding is not None]
            links_created = 0

            for idx, req in enumerate(reqs):
                job.progress = 45 + int((idx / len(reqs)) * 50)
                await session.commit()

                req_emb = list(req.embedding)
                scores = []
                for f in files_with_emb:
                    sim = _cosine(req_emb, list(f.embedding))
                    if sim >= MIN_SCORE:
                        scores.append((sim, f))

                scores.sort(key=lambda x: x[0], reverse=True)

                for score, f in scores[:TOP_K]:
                    link = TraceLink(
                        project_id=project_id,
                        source_type="requirement",
                        source_id=req.id,
                        target_type="code_file",
                        target_id=f.id,
                        link_type="implements",
                        confidence_score=round(float(score), 2),
                        status="suggested",
                        is_manual=False,
                    )
                    session.add(link)
                    links_created += 1

            await session.commit()

            job.status = "completed"
            job.progress = 100
            job.completed_at = datetime.utcnow()
            job.result_data = {
                "links_created": links_created,
                "requirements_processed": len(reqs),
                "files_indexed": len(files_with_emb),
            }
            await session.commit()

        except Exception as exc:
            logger.exception("generate_trace_links failed")
            job.status = "failed"
            job.error_message = str(exc)
            job.completed_at = datetime.utcnow()
            await session.commit()
            raise

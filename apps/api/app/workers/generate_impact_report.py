import asyncio
import json
import logging
import uuid
from datetime import datetime

from app.database import async_session_factory
from app.llm.prompts import IMPACT_SUMMARY_PROMPT, IMPACT_SUMMARY_SYSTEM
from app.llm.provider_factory import get_provider
from app.models.analysis_job import AnalysisJob
from app.services.impact_service import build_impact_report

logger = logging.getLogger(__name__)

SUMMARY_TIMEOUT = 60.0


def run_generate_impact_report(
    job_id: str, project_id: str, requirement_id: str, modification_description: str
) -> None:
    asyncio.run(
        _generate_impact_report(
            uuid.UUID(job_id),
            uuid.UUID(project_id),
            uuid.UUID(requirement_id),
            modification_description,
        )
    )


async def _generate_impact_report(
    job_id: uuid.UUID,
    project_id: uuid.UUID,
    requirement_id: uuid.UUID,
    modification_description: str,
) -> None:
    async with async_session_factory() as session:
        job = await session.get(AnalysisJob, job_id)
        if not job:
            return

        job.status = "running"
        job.started_at = datetime.utcnow()
        job.progress = 10
        await session.commit()

        try:
            report = await build_impact_report(session, project_id, requirement_id)
            job.progress = 60
            await session.commit()

            llm = get_provider()
            llm_ok = await llm.health_check()
            summary = None

            if llm_ok:
                prompt = IMPACT_SUMMARY_PROMPT.format(
                    req_code=report["requirement"]["code"],
                    req_title=report["requirement"]["title"],
                    req_description=report["requirement"]["description"] or "",
                    modification_description=modification_description,
                    direct_count=len(report["direct_files"]),
                    direct_files=", ".join(f["path"] for f in report["direct_files"]) or "aucun",
                    test_count=len(report["direct_tests"]),
                    direct_tests=", ".join(f["path"] for f in report["direct_tests"]) or "aucun",
                    indirect_count=len(report["indirect_requirements"]),
                    indirect_reqs=", ".join(r["code"] for r in report["indirect_requirements"])
                    or "aucune",
                    conflicts=", ".join(c["title"] for c in report["conflicts"]) or "aucun",
                )
                try:
                    response = await asyncio.wait_for(
                        llm.complete(prompt, system=IMPACT_SUMMARY_SYSTEM),
                        timeout=SUMMARY_TIMEOUT,
                    )
                    raw = response.content.strip()
                    if raw and not raw.endswith("}"):
                        raw = raw.rsplit(",", 1)[0] + "}"
                    summary = json.loads(raw).get("summary")
                except (asyncio.TimeoutError, json.JSONDecodeError, Exception) as e:
                    logger.warning("Impact summary failed: %s", e)

            report["modification_description"] = modification_description
            report["summary"] = summary

            job.status = "completed"
            job.progress = 100
            job.completed_at = datetime.utcnow()
            job.result_data = report
            await session.commit()

        except Exception as exc:
            logger.exception("generate_impact_report failed")
            job.status = "failed"
            job.error_message = str(exc)
            job.completed_at = datetime.utcnow()
            await session.commit()
            raise

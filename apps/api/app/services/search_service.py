import math
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.llm.provider_factory import get_provider
from app.models.code_file import CodeFile
from app.models.requirement import Requirement

MIN_SCORE = 0.35
TOP_K = 10


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


async def semantic_search(
    session: AsyncSession, project_id: uuid.UUID, query: str, target: str = "all"
) -> list[dict]:
    llm = get_provider()
    if not await llm.health_check():
        raise RuntimeError("LLM provider unavailable for semantic search")

    query_embedding = await llm.embed(query)

    results: list[tuple[float, dict]] = []

    if target in ("all", "requirement"):
        reqs_result = await session.execute(
            select(Requirement).where(
                Requirement.project_id == project_id,
                Requirement.embedding.is_not(None),
            )
        )
        for req in reqs_result.scalars().all():
            score = _cosine(query_embedding, list(req.embedding))
            if score >= MIN_SCORE:
                results.append(
                    (
                        score,
                        {
                            "type": "requirement",
                            "id": str(req.id),
                            "code": req.code,
                            "title": req.title,
                            "summary": req.description,
                            "score": round(score, 2),
                        },
                    )
                )

    if target in ("all", "code_file"):
        files_result = await session.execute(
            select(CodeFile).where(
                CodeFile.project_id == project_id,
                CodeFile.embedding.is_not(None),
            )
        )
        for f in files_result.scalars().all():
            score = _cosine(query_embedding, list(f.embedding))
            if score >= MIN_SCORE:
                results.append(
                    (
                        score,
                        {
                            "type": "code_file",
                            "id": str(f.id),
                            "code": f.path,
                            "title": f.path.rsplit("/", 1)[-1],
                            "summary": f.summary,
                            "score": round(score, 2),
                        },
                    )
                )

    results.sort(key=lambda x: x[0], reverse=True)
    return [r for _, r in results[:TOP_K]]

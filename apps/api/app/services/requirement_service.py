import re
import uuid
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.requirement import Requirement
from app.schemas.requirement import RequirementCreate, RequirementUpdate

# RULE-004 — ambiguous words without a numeric value
_AMBIGUOUS_WORDS = re.compile(
    r"\b(rapide|simple|robuste|performant|scalable|fiable|stable|efficace|léger|"
    r"fast|simple|robust|reliable|stable|efficient|lightweight|scalable)\b",
    re.IGNORECASE,
)
_HAS_METRIC = re.compile(r"\d+\s*(ms|s|min|h|%|rps|req/s|mb|gb|kb)", re.IGNORECASE)

# RULE-007 — performance requirement without numeric threshold
_PERF_METRIC = re.compile(r"\d+\s*(ms|s|min|%|rps|req/s)", re.IGNORECASE)


async def _next_code(session: AsyncSession, project_id: uuid.UUID) -> str:
    result = await session.execute(select(func.count()).where(Requirement.project_id == project_id))
    count = result.scalar_one()
    return f"REQ-{count + 1:03d}"


def _check_ambiguity(title: str, description: str, req_type: str) -> tuple[bool, Optional[str]]:
    text = f"{title} {description or ''}"
    if req_type == "performance" and not _PERF_METRIC.search(text):
        return True, "Exigence de performance sans seuil mesurable (ms, %, RPS, etc.)"
    match = _AMBIGUOUS_WORDS.search(text)
    if match and not _HAS_METRIC.search(text):
        return True, f"Terme ambigu « {match.group()} » sans métrique mesurable associée"
    return False, None


async def list_requirements(
    session: AsyncSession,
    project_id: uuid.UUID,
    req_type: Optional[str] = None,
    priority: Optional[str] = None,
    status: Optional[str] = None,
    is_ambiguous: Optional[bool] = None,
    search: Optional[str] = None,
) -> list[Requirement]:
    q = select(Requirement).where(Requirement.project_id == project_id)
    if req_type:
        q = q.where(Requirement.req_type == req_type)
    if priority:
        q = q.where(Requirement.priority == priority)
    if status:
        q = q.where(Requirement.status == status)
    if is_ambiguous is not None:
        q = q.where(Requirement.is_ambiguous == is_ambiguous)
    if search:
        pattern = f"%{search}%"
        q = q.where(Requirement.title.ilike(pattern) | Requirement.description.ilike(pattern))
    q = q.order_by(Requirement.code)
    result = await session.execute(q)
    return list(result.scalars().all())


async def get_requirement(
    session: AsyncSession, project_id: uuid.UUID, req_id: uuid.UUID
) -> Optional[Requirement]:
    result = await session.execute(
        select(Requirement).where(Requirement.id == req_id, Requirement.project_id == project_id)
    )
    return result.scalar_one_or_none()


async def create_requirement(
    session: AsyncSession,
    project_id: uuid.UUID,
    data: RequirementCreate,
    source_document_id: Optional[uuid.UUID] = None,
) -> Requirement:
    is_ambiguous, ambiguity_reason = _check_ambiguity(
        data.title, data.description or "", data.req_type
    )
    if data.is_ambiguous:
        is_ambiguous = True
        ambiguity_reason = data.ambiguity_reason or ambiguity_reason

    code = await _next_code(session, project_id)
    req = Requirement(
        project_id=project_id,
        code=code,
        title=data.title,
        description=data.description,
        req_type=data.req_type,
        priority=data.priority,
        is_ambiguous=is_ambiguous,
        ambiguity_reason=ambiguity_reason,
        source_document_id=source_document_id,
    )
    session.add(req)
    await session.commit()
    await session.refresh(req)
    return req


async def update_requirement(
    session: AsyncSession, req: Requirement, data: RequirementUpdate
) -> Requirement:
    updates = data.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(req, field, value)

    if "title" in updates or "description" in updates or "req_type" in updates:
        is_ambiguous, ambiguity_reason = _check_ambiguity(
            req.title, req.description or "", req.req_type
        )
        if not req.is_ambiguous:
            req.is_ambiguous = is_ambiguous
            req.ambiguity_reason = ambiguity_reason

    if "title" in updates or "description" in updates:
        req.status = "modified"
        req.version = (req.version or 1) + 1

    await session.commit()
    await session.refresh(req)
    return req


async def delete_requirement(session: AsyncSession, req: Requirement) -> None:
    await session.delete(req)
    await session.commit()

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.conflict import DetectedConflict
from app.schemas.conflict import ConflictUpdate, DetectedConflictResponse
from app.services.conflict_service import detect_conflicts
from app.services.project_service import get_project

router = APIRouter(prefix="/projects/{project_id}/conflicts", tags=["conflicts"])

_VALID_STATUSES = {"open", "resolved", "ignored"}


@router.get("", response_model=list[DetectedConflictResponse])
async def list_conflicts(
    project_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    project = await get_project(session, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    result = await session.execute(
        select(DetectedConflict)
        .where(DetectedConflict.project_id == project_id)
        .order_by(DetectedConflict.created_at.desc())
    )
    return list(result.scalars().all())


@router.post("/detect", response_model=list[DetectedConflictResponse])
async def run_conflict_detection(
    project_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    project = await get_project(session, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    await detect_conflicts(session, project_id)

    result = await session.execute(
        select(DetectedConflict)
        .where(DetectedConflict.project_id == project_id)
        .order_by(DetectedConflict.created_at.desc())
    )
    return list(result.scalars().all())


@router.patch("/{conflict_id}", response_model=DetectedConflictResponse)
async def update_conflict(
    project_id: uuid.UUID,
    conflict_id: uuid.UUID,
    data: ConflictUpdate,
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(DetectedConflict).where(
            DetectedConflict.id == conflict_id,
            DetectedConflict.project_id == project_id,
        )
    )
    conflict = result.scalar_one_or_none()
    if not conflict:
        raise HTTPException(status_code=404, detail="Conflict not found")

    if data.status not in _VALID_STATUSES:
        raise HTTPException(
            status_code=400, detail=f"Status must be one of: {', '.join(_VALID_STATUSES)}"
        )

    conflict.status = data.status
    if data.status == "resolved":
        conflict.resolved_at = datetime.utcnow()
    await session.commit()
    await session.refresh(conflict)
    return conflict

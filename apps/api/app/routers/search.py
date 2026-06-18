import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.schemas.search import SearchResult
from app.services.project_service import get_project
from app.services.search_service import semantic_search

router = APIRouter(prefix="/projects/{project_id}/search", tags=["search"])


@router.get("", response_model=list[SearchResult])
async def search(
    project_id: uuid.UUID,
    q: str = Query(..., min_length=1),
    target: str = Query("all", pattern="^(all|requirement|code_file)$"),
    session: AsyncSession = Depends(get_session),
):
    project = await get_project(session, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        return await semantic_search(session, project_id, q, target)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e

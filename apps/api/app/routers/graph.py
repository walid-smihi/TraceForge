import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.schemas.graph import GraphResponse, ProjectMetrics
from app.services import graph_service
from app.services.project_service import get_project

router = APIRouter(prefix="/projects/{project_id}", tags=["graph"])


@router.get("/graph", response_model=GraphResponse)
async def get_graph(project_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    project = await get_project(session, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return await graph_service.build_graph(session, project_id)


@router.get("/metrics", response_model=ProjectMetrics)
async def get_metrics(project_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    project = await get_project(session, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return await graph_service.get_metrics(session, project_id)

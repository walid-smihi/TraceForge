from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import (
    documents,
    export,
    graph,
    jobs,
    projects,
    repositories,
    requirements,
    trace_links,
)
from app.routers import (
    settings as settings_router,
)
from config import settings

app = FastAPI(
    title="TraceForge API",
    version="0.1.0",
    docs_url="/docs" if settings.APP_ENV != "production" else None,
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects.router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1")
app.include_router(requirements.router, prefix="/api/v1")
app.include_router(repositories.router, prefix="/api/v1")
app.include_router(trace_links.router, prefix="/api/v1")
app.include_router(graph.router, prefix="/api/v1")
app.include_router(jobs.router, prefix="/api/v1")
app.include_router(export.router, prefix="/api/v1")
app.include_router(settings_router.router, prefix="/api/v1")


@app.get("/health", tags=["system"])
async def health() -> dict:
    return {"status": "ok", "version": "0.1.0"}

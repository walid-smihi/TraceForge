from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import app.models  # noqa: F401 — register all models on Base before create_all
from app.database import engine, init_db
from app.routers import (
    conflicts,
    documents,
    export,
    graph,
    impact,
    jobs,
    projects,
    repositories,
    requirements,
    search,
    trace_links,
)
from app.routers import (
    settings as settings_router,
)
from config import settings


@asynccontextmanager
async def lifespan(_app: FastAPI):
    Path(settings.STORAGE_PATH).mkdir(parents=True, exist_ok=True)
    if engine.url.get_backend_name() == "sqlite" and engine.url.database:
        Path(engine.url.database).parent.mkdir(parents=True, exist_ok=True)
    await init_db()
    yield


app = FastAPI(
    title="TraceForge API",
    version="0.1.0",
    docs_url="/docs" if settings.APP_ENV != "production" else None,
    redoc_url=None,
    lifespan=lifespan,
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
app.include_router(conflicts.router, prefix="/api/v1")
app.include_router(impact.router, prefix="/api/v1")
app.include_router(search.router, prefix="/api/v1")
app.include_router(jobs.router, prefix="/api/v1")
app.include_router(export.router, prefix="/api/v1")
app.include_router(settings_router.router, prefix="/api/v1")


@app.get("/health", tags=["system"])
async def health() -> dict:
    return {"status": "ok", "version": "0.1.0"}

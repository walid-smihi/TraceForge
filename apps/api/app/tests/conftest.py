import os

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import app.models  # noqa: F401 — register all models
from app.database import Base, get_session
from main import app

TEST_DB_URL = os.environ.get(
    "DATABASE_URL", "postgresql+asyncpg://traceforge:traceforgedev@localhost:5433/traceforge_test"
)

if "test" not in TEST_DB_URL.rsplit("/", 1)[-1]:
    raise RuntimeError(
        f"Refusing to run tests against a database without 'test' in its name: {TEST_DB_URL!r}. "
        "This fixture suite drops all tables on teardown — pointing it at a real database "
        "destroys data. Use a dedicated *_test database."
    )

test_engine = create_async_engine(TEST_DB_URL, echo=False)
test_session_factory = async_sessionmaker(test_engine, expire_on_commit=False)


@pytest.fixture(scope="session", autouse=True)
async def setup_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(autouse=True)
async def clean_db():
    yield
    async with test_engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())


@pytest.fixture
async def session() -> AsyncSession:
    async with test_session_factory() as s:
        yield s


@pytest.fixture
async def client(session: AsyncSession) -> AsyncClient:
    app.dependency_overrides[get_session] = lambda: session
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()

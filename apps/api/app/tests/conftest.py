import os
import tempfile

# A real file (not :memory:) is required: worker code under test opens its
# own session via app.database's module-level engine — only a shared file on
# disk lets that engine and this module's test_engine see the same data.
# This must be set before app.database (and anything importing it) loads,
# since config.settings reads DATABASE_URL once at import time.
_TEST_DB_PATH = os.path.join(tempfile.mkdtemp(prefix="traceforge-test-"), "test.db")
TEST_DB_URL = os.environ.setdefault("DATABASE_URL", f"sqlite+aiosqlite:///{_TEST_DB_PATH}")

if "test" not in TEST_DB_URL.rsplit("/", 1)[-1]:
    raise RuntimeError(
        f"Refusing to run tests against a database without 'test' in its name: {TEST_DB_URL!r}. "
        "This fixture suite drops all tables on teardown — pointing it at a real database "
        "destroys data. Use a dedicated *_test database."
    )

import pytest  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy import event  # noqa: E402
from sqlalchemy.ext.asyncio import (  # noqa: E402
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

import app.models  # noqa: E402,F401 — register all models
from app.database import Base, get_session  # noqa: E402
from main import app  # noqa: E402

test_engine = create_async_engine(TEST_DB_URL, echo=False)

if test_engine.url.get_backend_name() == "sqlite":

    @event.listens_for(test_engine.sync_engine, "connect")
    def _enable_test_sqlite_foreign_keys(dbapi_connection, _connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


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

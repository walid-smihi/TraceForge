from collections.abc import AsyncGenerator

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from config import settings


class Base(DeclarativeBase):
    pass


engine = create_async_engine(settings.DATABASE_URL, echo=settings.APP_ENV == "development")
async_session_factory = async_sessionmaker(engine, expire_on_commit=False)


if engine.url.get_backend_name() == "sqlite":

    @event.listens_for(engine.sync_engine, "connect")
    def _configure_sqlite_connection(dbapi_connection, _connection_record) -> None:
        cursor = dbapi_connection.cursor()
        # SQLite ignores ON DELETE CASCADE unless foreign key enforcement is
        # explicitly turned on for every connection.
        cursor.execute("PRAGMA foreign_keys=ON")
        # WAL allows the backend and worker process to both hold open
        # connections to the same file without "database is locked" errors.
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session

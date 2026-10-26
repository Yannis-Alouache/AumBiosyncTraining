"""Database access: SQLAlchemy async engine, session per request, schema.

Repositories use `get_session()` to run ORM queries; the session is bound
to the request context and closed on teardown. `init_db` creates the
schema from the ORM metadata (app/models.py is the source of truth).

Convention: timestamps are stored as local naive ISO 8601 strings (no
timezone), which sort lexicographically. This is a deliberate
simplification for this demo database; see README.
"""

from pathlib import Path

from quart import current_app, g
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models import Base


def create_engine_for(database_path: str):
    """Async engine for an SQLite file, with pragmas applied per connection."""
    url = f"sqlite+aiosqlite:///{Path(database_path).as_posix()}"
    engine = create_async_engine(url)

    @event.listens_for(engine.sync_engine, "connect")
    def _apply_sqlite_pragmas(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.execute("PRAGMA journal_mode = WAL")
        cursor.close()

    return engine


def bind_engine(app) -> None:
    """Attaches the engine and the session factory to the application."""
    engine = create_engine_for(app.config["DATABASE"])
    app.extensions["db_engine"] = engine
    app.extensions["db_session_factory"] = async_sessionmaker(engine, expire_on_commit=False)


async def init_db(database_path: str) -> None:
    """Creates the schema from the ORM metadata. Idempotent, safe in dev and
    in tests."""
    engine = create_engine_for(database_path)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    await engine.dispose()


async def get_session() -> AsyncSession:
    """Session bound to the request context (opened on first use)."""
    if "db_session" not in g:
        factory = current_app.extensions["db_session_factory"]
        g.db_session = factory()
    return g.db_session


async def close_db(_exc) -> None:
    """Closes the request session at the end of the request."""
    session = g.pop("db_session", None)
    if session is not None:
        await session.close()

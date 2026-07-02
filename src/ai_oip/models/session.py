"""Async database engine and session management.

Engine creation is parameterized by URL (not by reading `Settings`
directly) so tests can point it at SQLite without needing a real
Postgres instance, while production code goes through
`create_engine_from_settings`, which is the only function that reads
`Settings.database_url`.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from ai_oip.config import Settings


def create_engine(database_url: str, *, echo: bool = False) -> AsyncEngine:
    """Create an async SQLAlchemy engine for the given connection string."""
    return create_async_engine(database_url, echo=echo)


def create_engine_from_settings(settings: Settings) -> AsyncEngine:
    """Create the application's async engine from validated Settings.

    The only place `Settings.database_url` is read to build an engine —
    everything else receives a session, never a raw connection string.
    """
    return create_engine(settings.database_url, echo=settings.debug)


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Create a session factory bound to the given engine.

    `expire_on_commit=False` so objects returned by a repository remain
    usable (e.g. read after `save()`) without triggering an implicit
    reload — repositories, not callers, own transaction boundaries.
    """
    return async_sessionmaker(bind=engine, expire_on_commit=False)


@asynccontextmanager
async def session_scope(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncSession, None]:
    """Provide a transactional session: commits on success, rolls back on error.

    Usage:
        async with session_scope(session_factory) as session:
            repo = SQLAlchemyRepository(session, SomeModel)
            await repo.save(entity)
    """
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

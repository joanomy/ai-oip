"""Shared pytest fixtures.

Database tests use an in-memory SQLite engine, not Postgres — see
ADR-0005 for the trade-off this implies (SQLite exercises the same
SQLAlchemy code path but not Postgres-specific behavior). A real
Postgres integration test is a documented Future Improvement, not an
oversight.
"""

from collections.abc import AsyncGenerator

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from ai_oip.models.base import Base
from ai_oip.models.session import create_engine, create_session_factory
from tests.fixtures.models import DemoRecord  # noqa: F401  (registers the table)


@pytest_asyncio.fixture
async def db_engine() -> AsyncGenerator[AsyncEngine, None]:
    """A fresh in-memory SQLite engine with all tables created, per test."""
    engine = create_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """An AsyncSession bound to the per-test in-memory engine."""
    session_factory = create_session_factory(db_engine)
    async with session_factory() as session:
        yield session

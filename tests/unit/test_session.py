"""Tests for database session/engine management (Milestone 4)."""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncEngine

from ai_oip.config import Settings
from ai_oip.models.session import (
    create_engine_from_settings,
    create_session_factory,
    session_scope,
)
from ai_oip.repositories import SQLAlchemyRepository
from tests.fixtures.models import DemoRecord

pytestmark = pytest.mark.asyncio


async def test_create_engine_from_settings_uses_database_url() -> None:
    settings = Settings(
        _env_file=None,
        database_url="postgresql+asyncpg://user:pass@localhost:5432/testdb",
    )

    engine = create_engine_from_settings(settings)

    assert isinstance(engine, AsyncEngine)
    assert str(engine.url).startswith("postgresql+asyncpg://")
    await engine.dispose()


async def test_session_scope_commits_on_success(db_engine: AsyncEngine) -> None:
    session_factory = create_session_factory(db_engine)

    async with session_scope(session_factory) as session:
        repo = SQLAlchemyRepository(session, DemoRecord)
        await repo.save(DemoRecord(value="committed"))

    # New session, outside the context manager: the commit should be visible.
    async with session_factory() as verify_session:
        result = await verify_session.execute(select(DemoRecord))
        rows = result.scalars().all()

    assert len(rows) == 1
    assert rows[0].value == "committed"


async def test_session_scope_rolls_back_on_exception(db_engine: AsyncEngine) -> None:
    session_factory = create_session_factory(db_engine)

    with pytest.raises(ValueError, match="boom"):
        async with session_scope(session_factory) as session:
            repo = SQLAlchemyRepository(session, DemoRecord)
            await repo.save(DemoRecord(value="should_not_persist"))
            raise ValueError("boom")

    async with session_factory() as verify_session:
        result = await verify_session.execute(select(DemoRecord))
        rows = result.scalars().all()

    assert len(rows) == 0

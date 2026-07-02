"""Integration tests: the repository layer against a real Postgres.

Closes the SQLite-only trade-off accepted in ADR-0005: these exercise
the same code paths as the unit suite but against actual Postgres
semantics (server-side now(), real dialect, real driver). Gated on
INTEGRATION_DATABASE_URL — set by CI's Postgres service container, or
locally via `docker compose up postgres` plus the URL from
docker-compose.yml. Skipped (not failed) when unset, so the local
quality gate never requires Docker.
"""

import os
from uuid import uuid4

import pytest
import pytest_asyncio

from ai_oip.models.base import Base
from ai_oip.models.session import create_engine, create_session_factory, session_scope
from ai_oip.repositories import SQLAlchemyRepository
from tests.fixtures.models import DemoRecord

INTEGRATION_URL = os.environ.get("INTEGRATION_DATABASE_URL")

pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.integration,
    pytest.mark.skipif(
        not INTEGRATION_URL,
        reason="INTEGRATION_DATABASE_URL not set (start Postgres via docker compose)",
    ),
]


@pytest_asyncio.fixture
async def pg_session_factory():
    engine = create_engine(INTEGRATION_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield create_session_factory(engine)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


async def test_full_crud_roundtrip_on_postgres(pg_session_factory) -> None:
    async with session_scope(pg_session_factory) as session:
        repo = SQLAlchemyRepository(session, DemoRecord)
        saved = await repo.save(DemoRecord(value="postgres-roundtrip"))
        saved_id = saved.id

    async with session_scope(pg_session_factory) as session:
        repo = SQLAlchemyRepository(session, DemoRecord)
        fetched = await repo.get_by_id(saved_id)
        assert fetched is not None
        assert fetched.value == "postgres-roundtrip"

        await repo.delete(saved_id)

    async with session_scope(pg_session_factory) as session:
        repo = SQLAlchemyRepository(session, DemoRecord)
        assert await repo.get_by_id(saved_id) is None


async def test_server_side_timestamps_are_set_by_postgres(pg_session_factory) -> None:
    # server_default=func.now() is exactly the kind of behavior SQLite
    # can't prove — Postgres itself must fill these columns.
    async with session_scope(pg_session_factory) as session:
        repo = SQLAlchemyRepository(session, DemoRecord)
        saved = await repo.save(DemoRecord(value="timestamped"))

        assert saved.created_at is not None
        assert saved.updated_at is not None
        assert saved.created_at.tzinfo is not None  # timestamptz, not naive


async def test_rollback_discards_uncommitted_rows_on_postgres(pg_session_factory) -> None:
    with pytest.raises(RuntimeError, match="abort"):
        async with session_scope(pg_session_factory) as session:
            repo = SQLAlchemyRepository(session, DemoRecord)
            await repo.save(DemoRecord(value="never-committed"))
            raise RuntimeError("abort")

    async with session_scope(pg_session_factory) as session:
        repo = SQLAlchemyRepository(session, DemoRecord)
        assert await repo.list_all() == []


async def test_get_missing_id_returns_none_on_postgres(pg_session_factory) -> None:
    async with session_scope(pg_session_factory) as session:
        repo = SQLAlchemyRepository(session, DemoRecord)
        assert await repo.get_by_id(uuid4()) is None

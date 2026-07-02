"""Tests for SQLAlchemyRepository (Milestone 4).

These run against a real (in-memory SQLite) database via the
`db_session` fixture — not mocks — proving the repository pattern
established in M1 actually works against a real ORM/database, not
just the abstract interface.
"""

from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from ai_oip.core.exceptions import RepositoryError
from ai_oip.repositories import BaseRepository, SQLAlchemyRepository
from tests.fixtures.models import DemoRecord

pytestmark = pytest.mark.asyncio


async def test_sqlalchemy_repository_implements_base_repository(
    db_session: AsyncSession,
) -> None:
    repo = SQLAlchemyRepository(db_session, DemoRecord)

    assert isinstance(repo, BaseRepository)


async def test_save_persists_and_assigns_timestamps(db_session: AsyncSession) -> None:
    repo = SQLAlchemyRepository(db_session, DemoRecord)
    record = DemoRecord(value="hello")

    saved = await repo.save(record)

    assert saved.id is not None
    assert saved.created_at is not None
    assert saved.updated_at is not None
    assert saved.value == "hello"


async def test_get_by_id_returns_saved_entity(db_session: AsyncSession) -> None:
    repo = SQLAlchemyRepository(db_session, DemoRecord)
    saved = await repo.save(DemoRecord(value="findme"))

    fetched = await repo.get_by_id(saved.id)

    assert fetched is not None
    assert fetched.id == saved.id
    assert fetched.value == "findme"


async def test_get_by_id_returns_none_for_missing_entity(db_session: AsyncSession) -> None:
    repo = SQLAlchemyRepository(db_session, DemoRecord)

    result = await repo.get_by_id(uuid4())

    assert result is None


async def test_delete_removes_entity(db_session: AsyncSession) -> None:
    repo = SQLAlchemyRepository(db_session, DemoRecord)
    saved = await repo.save(DemoRecord(value="temporary"))

    await repo.delete(saved.id)
    result = await repo.get_by_id(saved.id)

    assert result is None


async def test_delete_missing_entity_is_idempotent(db_session: AsyncSession) -> None:
    repo = SQLAlchemyRepository(db_session, DemoRecord)

    await repo.delete(uuid4())  # should not raise


async def test_list_all_returns_every_row(db_session: AsyncSession) -> None:
    repo = SQLAlchemyRepository(db_session, DemoRecord)
    await repo.save(DemoRecord(value="one"))
    await repo.save(DemoRecord(value="two"))

    results = await repo.list_all()

    assert {r.value for r in results} == {"one", "two"}


async def test_save_failure_raises_repository_error(db_session: AsyncSession) -> None:
    repo = SQLAlchemyRepository(db_session, DemoRecord)
    # value is non-nullable; omitting it should fail at flush time.
    invalid_record = DemoRecord()

    with pytest.raises(RepositoryError):
        await repo.save(invalid_record)

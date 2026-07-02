"""Unit tests for the BaseRepository contract.

Uses a minimal in-memory dummy repository to prove the abstract
interface is implementable and behaves as intended. This same pattern
is what `services/` tests use to avoid depending on a real database.
"""

from dataclasses import dataclass
from uuid import UUID, uuid4

import pytest

from ai_oip.repositories.base import BaseRepository


@dataclass
class _DummyEntity:
    id: UUID
    value: str


class _InMemoryRepository(BaseRepository[_DummyEntity]):
    """Test-only repository: no database, just a dict."""

    def __init__(self) -> None:
        self._store: dict[UUID, _DummyEntity] = {}

    async def get_by_id(self, entity_id: UUID) -> _DummyEntity | None:
        return self._store.get(entity_id)

    async def save(self, entity: _DummyEntity) -> _DummyEntity:
        self._store[entity.id] = entity
        return entity

    async def delete(self, entity_id: UUID) -> None:
        self._store.pop(entity_id, None)


def test_base_repository_cannot_be_instantiated_directly() -> None:
    with pytest.raises(TypeError):
        BaseRepository()  # type: ignore[abstract]


async def test_concrete_repository_save_and_get() -> None:
    repo = _InMemoryRepository()
    entity = _DummyEntity(id=uuid4(), value="test")

    saved = await repo.save(entity)
    fetched = await repo.get_by_id(entity.id)

    assert saved == entity
    assert fetched == entity


async def test_concrete_repository_get_missing_returns_none() -> None:
    repo = _InMemoryRepository()

    assert await repo.get_by_id(uuid4()) is None


async def test_concrete_repository_delete_is_idempotent() -> None:
    repo = _InMemoryRepository()
    entity = _DummyEntity(id=uuid4(), value="test")
    await repo.save(entity)

    await repo.delete(entity.id)
    await repo.delete(entity.id)  # deleting again should not raise

    assert await repo.get_by_id(entity.id) is None

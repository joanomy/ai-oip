"""Generic SQLAlchemy implementation of the BaseRepository contract.

This is a platform capability, not a one-off: any future SQLAlchemy
model gets `get_by_id` / `save` / `delete` for free by instantiating
(or subclassing) `SQLAlchemyRepository[ModelType]` — no concrete
repository needs to reimplement basic CRUD against the database.

Concrete repositories subclass this only to add domain-specific query
methods (e.g. `get_by_email`), which is expected and fine — the base
class is deliberately minimal, matching `BaseRepository`'s contract.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ai_oip.core.exceptions import RepositoryError
from ai_oip.models.base import Base
from ai_oip.repositories.base import BaseRepository


class SQLAlchemyRepository[Entity: Base](BaseRepository[Entity]):
    """Generic async repository backed by a SQLAlchemy session.

    Type parameter `Entity` must be a `Base`-derived ORM model with a
    UUID `id` column (i.e. it should use `UUIDPrimaryKeyMixin`).
    """

    def __init__(self, session: AsyncSession, model: type[Entity]) -> None:
        self._session = session
        self._model = model

    # Every method wraps failures in RepositoryError — not just save().
    # The exception hierarchy exists so autonomous pipelines can catch
    # failures by category (retry/skip/halt); a read failure escaping as
    # a raw SQLAlchemy exception would defeat that categorization
    # exactly where it matters most.

    async def get_by_id(self, entity_id: UUID) -> Entity | None:
        try:
            return await self._session.get(self._model, entity_id)
        except Exception as exc:
            raise RepositoryError(f"Failed to fetch {self._model.__name__} by id: {exc}") from exc

    async def save(self, entity: Entity) -> Entity:
        try:
            self._session.add(entity)
            await self._session.flush()
            await self._session.refresh(entity)
        except Exception as exc:
            raise RepositoryError(f"Failed to save {self._model.__name__}: {exc}") from exc
        return entity

    async def delete(self, entity_id: UUID) -> None:
        entity = await self.get_by_id(entity_id)
        if entity is None:
            return
        try:
            await self._session.delete(entity)
            await self._session.flush()
        except Exception as exc:
            raise RepositoryError(f"Failed to delete {self._model.__name__}: {exc}") from exc

    async def list_all(self) -> list[Entity]:
        """List all rows for this model.

        Not part of `BaseRepository` (which stays deliberately minimal),
        but common enough across concrete repositories to belong here
        rather than being reimplemented per-repository.
        """
        try:
            result = await self._session.execute(select(self._model))
            return list(result.scalars().all())
        except Exception as exc:
            raise RepositoryError(f"Failed to list {self._model.__name__}: {exc}") from exc

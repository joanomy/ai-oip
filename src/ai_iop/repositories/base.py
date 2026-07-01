"""Base repository interface.

This is the only layer in the application permitted to import from
`ai_iop.models` and hold a database session. Services and pipelines
depend on repositories through this interface; agents never do.
"""

from abc import ABC, abstractmethod
from uuid import UUID


class BaseRepository[Entity](ABC):
    """Abstract base class all repositories must inherit from.

    Concrete repositories (Milestone 4) implement these against a real
    SQLAlchemy async session. This interface exists now so that
    `services/` can be written and tested against a fake/in-memory
    repository before the real database layer exists.
    """

    @abstractmethod
    async def get_by_id(self, entity_id: UUID) -> Entity | None:
        """Fetch a single entity by ID, or None if it doesn't exist."""
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    async def save(self, entity: Entity) -> Entity:
        """Persist a new or updated entity and return the saved state."""
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    async def delete(self, entity_id: UUID) -> None:
        """Delete an entity by ID. No-op if it doesn't exist."""
        raise NotImplementedError  # pragma: no cover

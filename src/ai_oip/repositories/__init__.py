"""Repositories: the ONLY layer allowed to query the database.

Wraps `models/` behind explicit methods (e.g., get_by_id, save). Services
and pipelines depend on repositories; agents never do.

`SQLAlchemyRepository` is the generic, reusable implementation every
concrete repository should use or subclass rather than reimplementing
CRUD against the database.

Dependency rule: depends on models, core.
"""

from ai_oip.repositories.base import BaseRepository
from ai_oip.repositories.problem_repository import ProblemRepository
from ai_oip.repositories.sqlalchemy_repository import SQLAlchemyRepository

__all__ = ["BaseRepository", "ProblemRepository", "SQLAlchemyRepository"]

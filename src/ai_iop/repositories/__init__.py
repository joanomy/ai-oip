"""Repositories: the ONLY layer allowed to query the database.

Wraps `models/` behind explicit methods (e.g., get_by_id, save). Services
and pipelines depend on repositories; agents never do.

Dependency rule: depends on models, core.
"""

from ai_iop.repositories.base import BaseRepository

__all__ = ["BaseRepository"]

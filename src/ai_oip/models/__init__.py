"""Models: SQLAlchemy ORM models describing data AT REST.

Defines how data is stored in the database, plus engine/session
management (session.py) and shared base/mixins (base.py). Never
imported outside of `repositories/` — no other layer touches the ORM
or holds a database session directly.

Dependency rule: depends only on core.
"""

from ai_oip.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from ai_oip.models.problem import ProblemRecord
from ai_oip.models.session import (
    create_engine,
    create_engine_from_settings,
    create_session_factory,
    session_scope,
)
from ai_oip.models.workflow import WorkflowRecord

__all__ = [
    "Base",
    "ProblemRecord",
    "TimestampMixin",
    "UUIDPrimaryKeyMixin",
    "WorkflowRecord",
    "create_engine",
    "create_engine_from_settings",
    "create_session_factory",
    "session_scope",
]

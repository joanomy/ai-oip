"""SQLAlchemy declarative base and reusable model mixins.

Every future ORM model in `ai_oip.models` inherits from `Base` and
typically from `UUIDPrimaryKeyMixin` and `TimestampMixin` — written
once here so no concrete model reimplements "how do I add an id and
timestamps" from scratch.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Root declarative base. All ORM models inherit from this.

    A single shared `Base` means `Base.metadata` reflects every table
    in the platform — this is what Alembic autogenerate compares
    against to produce migrations.
    """


class UUIDPrimaryKeyMixin:
    """Adds a UUID primary key column named `id`.

    UUIDs (not auto-increment integers) are the default here because
    they're safe to generate client-side, don't leak row counts, and
    don't collide across environments (useful once there's more than
    one database, e.g. a staging copy seeded from prod exports).
    """

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )


class TimestampMixin:
    """Adds `created_at` / `updated_at`, both set by the database.

    Using `server_default=func.now()` (not a Python-side default)
    means the timestamp is correct even for rows inserted outside the
    application (manual SQL, migrations, another service later).
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

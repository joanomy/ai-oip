"""Alembic migration environment.

Deliberately reads the database URL from `ai_oip.config.get_settings()`
rather than `alembic.ini` — migrations must run against the same
validated configuration the application itself uses, never a
separately-maintained connection string that can drift out of sync.

This file lives outside `src/ai_oip/` (import-linter's `root_package`),
so its direct import of `ai_oip.models` below is invisible to the
"models is only imported by repositories" contract. That's a known,
deliberate exception — Alembic's autogenerate needs direct access to
`Base.metadata` — not an accidental boundary violation. See ADR-0005.
"""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncEngine

from ai_oip.config import get_settings
from ai_oip.models.base import Base
from ai_oip.models.session import create_engine

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Every ORM model must be imported somewhere before this line runs, or
# Alembic's autogenerate won't see it. Concrete models (added as
# business milestones land) should be imported in ai_oip.models.__init__
# so this stays correct without editing this file per new model.
target_metadata = Base.metadata


def get_url() -> str:
    """Resolve the database URL from validated application Settings."""
    return get_settings().database_url


def run_migrations_offline() -> None:
    """Run migrations without a live DB connection (generates SQL only)."""
    context.configure(
        url=get_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def _run_migrations_sync(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations against a live async database connection."""
    connectable: AsyncEngine = create_engine(get_url())

    async with connectable.connect() as connection:
        await connection.run_sync(_run_migrations_sync)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())

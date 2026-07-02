# ADR-0005: Database Layer (SQLAlchemy Async + Alembic)

**Status:** Accepted
**Date:** 2026-07-02
**Milestone:** M4 — Database Layer

## Context
The repository pattern was established in M1 as an interface
(`BaseRepository`) and validated against an in-memory dummy. This
milestone builds the real implementation: async SQLAlchemy models,
migrations, and a generic repository that works against an actual
database engine.

Separately, the project was renamed `ai_iop` → `ai_oip` during this
milestone, correcting the acronym letter order to match the full name
word order: **O**pportunity **I**ntelligence **P**latform.

## Decisions

### 1. SQLAlchemy 2.0 async + asyncpg (production), aiosqlite (tests)
Async throughout, matching the platform's async-first stance
established for agents (M1) and logging (M3). `asyncpg` is the
production driver; `Settings.database_url` is validated to reject any
non-`asyncpg` connection string at startup (see M2/M4 `Settings`
validators) — a sync driver would silently block the event loop the
first time a repository issued a query.

### 2. `SQLAlchemyRepository[Entity]`: one generic implementation,
not one repository per future entity. Implements `BaseRepository`'s
full contract (`get_by_id`, `save`, `delete`) plus `list_all` (common
enough to include, kept out of the abstract interface to keep it
minimal). Concrete future repositories use this directly or subclass
it to add domain-specific queries — the reusable mechanics are built
once, here, rather than reimplemented per entity.

### 3. Testing against SQLite (aiosqlite), not a live Postgres
**This is a real, acknowledged trade-off, not an equivalence claim.**
SQLite exercises the same SQLAlchemy Core/ORM code paths (session
lifecycle, transaction commit/rollback, the repository implementation
itself) but does **not** catch Postgres-specific behavior — JSONB
operators, specific constraint/locking semantics, connection pooling
under concurrency. A real Postgres integration test (via a CI service
container or Docker Compose) is deferred to M9 (Dockerization), where
a real Postgres instance becomes available in the pipeline anyway.
Building that infrastructure now, before it's needed, would be
premature.

### 4. Alembic driven entirely by `Settings`, not `alembic.ini`
`migrations/env.py` reads `get_settings().database_url` — migrations
always run against the same validated configuration the application
uses. `alembic.ini` deliberately has no `sqlalchemy.url` line.
Verified working in both modes during this milestone:
- **Online mode** (`alembic revision --autogenerate`): confirmed it
  correctly loads config, resolves `Base.metadata`, and attempts a
  real connection — failing only with `ConnectionRefusedError`
  because no Postgres server exists in the build sandbox. This
  confirms the wiring is correct up to the point where a real
  database is genuinely required.
- **Offline mode** (`alembic upgrade head --sql`): fully verified
  end-to-end, generating dialect-correct SQL without needing a live
  connection.

### 5. `UUIDPrimaryKeyMixin` / `TimestampMixin` in `models/base.py`
Every future model gets a UUID primary key (safe to generate
client-side, doesn't leak row counts, doesn't collide across
environments) and `created_at`/`updated_at` set via
`server_default=func.now()` (correct even for rows inserted outside
the application, e.g. by a migration or another future service).

### 6. `migrations/env.py` is a deliberate, documented exception to import-linter
`import-linter`'s `root_package = "ai_oip"` only analyzes files under
`src/ai_oip/`. `migrations/env.py` sits outside that root, so its direct
import of `ai_oip.models` (needed for Alembic's autogenerate to see
`Base.metadata`) is invisible to the "models is only imported by
repositories" contract — not a gap in the contract's coverage that was
missed, but a boundary the tool was never going to enforce, now called
out explicitly rather than left implicit. No other code outside
`repositories/` should follow this precedent without the same
justification (Alembic tooling, not application logic).

## Consequences
- Any concrete future model inherits `Base`, `UUIDPrimaryKeyMixin`,
  `TimestampMixin` — established once, not reinvented per entity.
- The generic repository means adding a new entity's data-access layer
  is, in the common case, `SQLAlchemyRepository(session, NewModel)` —
  no new repository class required unless domain-specific queries are
  needed.
- Real Postgres integration testing remains a documented gap until M9.
  If a Postgres-specific bug ships before then, this is the first
  place to look.

## Revisit When
- M9 (Dockerization): add a Postgres service container to CI and at
  least one integration test exercising a JSONB column or a
  concurrency-sensitive constraint — the two categories SQLite testing
  cannot currently validate.
- The first concrete business model is added (M6+): confirm it fits
  the `UUIDPrimaryKeyMixin`/`TimestampMixin` pattern before deviating.

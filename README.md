# AI-OIP

Production-grade Python platform for autonomously executing AI workflows via
modular, single-responsibility agents.

**Status:** Milestone 4 (Database Layer) complete. Async SQLAlchemy +
Alembic, generic `SQLAlchemyRepository` proven against a real (SQLite)
database. No concrete business models or agents exist yet.

## Setup

```bash
# 1. Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Install dependencies (creates .venv automatically)
uv sync --all-groups

# 3. Install git hooks
uv run pre-commit install

# 4. Copy env template
cp .env.example .env
```

## Development Commands

```bash
uv run ruff check .              # lint
uv run ruff format .             # format
uv run mypy src                  # type check
uv run lint-imports               # verify architecture boundaries
uv run pytest                    # test with coverage
uv run pre-commit run --all-files  # run all hooks manually
uv run alembic revision --autogenerate -m "message"  # generate a migration
uv run alembic upgrade head      # apply migrations
```

## Architecture

AI-OIP is a **modular monolith**: one repository, one deployment, but
internally split into layers with enforced, one-directional dependencies.
`import-linter` fails CI if a lower layer imports a higher one (see
`pyproject.toml` `[tool.importlinter]` and `docs/architecture/ADR-0002`,
`ADR-0004` for why the layer order looks the way it does).

```
src/ai_oip/
├── pipelines/      # orchestrates services into end-to-end workflows
├── services/       # business logic; the only layer that knows both
│                     agents and repositories
├── collectors/     # external data ingestion
├── agents/         # single-responsibility AI units (never touch the DB)
├── repositories/   # the ONLY layer allowed to query the database
├── models/         # SQLAlchemy ORM — data at rest
├── schemas/        # Pydantic — data in motion (agent I/O, API I/O)
├── prompts/        # versioned prompt templates, external to code
├── logging/        # structured logging (depends on config)
├── monitoring/     # health checks, metrics (depends on config)
├── config/         # typed settings — depends only on core
└── core/           # shared exceptions/types — depended on by everything
```

## Project Status & Roadmap

See `docs/architecture/` for Architecture Decision Records (ADRs) explaining
*why* each engineering decision was made, not just what it is.

Milestones are executed one at a time: Architecture → Implementation →
Testing → Documentation → Review → Approval. Nothing is skipped.

| Milestone | Status |
|---|---|
| M0 — Environment & Repo Bootstrap | ✅ Complete |
| M1 — Project Architecture & Folder Structure | ✅ Complete |
| M2 — Configuration Management | ✅ Complete |
| M3 — Logging & Observability | ✅ Complete |
| M4 — Database Layer | ✅ Complete |
| M5 — Prompt Management | ⏳ Next |
| M6 — Agent Framework Core | Not started |
| M7 — Inter-Module Communication | Not started |
| M8 — Testing Framework | Not started |
| M9 — Dockerization | Not started |
| M10 — CI/CD Readiness | Not started |
| M11 — Monitoring & Health Checks | Not started |
| M12 — Documentation System | Ongoing |

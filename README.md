# AI-OIP

Production-grade Python platform for autonomously executing AI workflows via
modular, single-responsibility agents.

**Status:** Platform (M0–M7) plus five pipeline stages (M8–M12)
complete, driven by one CLI: `ai-oip discover "<query>"` →
`ai-oip workflows` → `ai-oip score` → `ai-oip research` →
`ai-oip recommend` (build/watch/pass plans for scored,
competition-assessed opportunities). Next up: M13 ICP Generator.

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
uv run pytest                    # test with coverage (integration tests skip without Postgres)
uv run pre-commit run --all-files  # run all hooks manually
uv run alembic revision --autogenerate -m "message"  # generate a migration
uv run alembic upgrade head      # apply migrations
```

### Real-Postgres integration tests (optional locally, always on in CI)

```bash
docker compose up -d postgres
INTEGRATION_DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/ai_oip_test uv run pytest tests/integration
```

### Run the walking skeleton (first end-to-end slice)

```bash
docker compose up -d postgres
uv run alembic upgrade head            # DATABASE_URL must point at your Postgres
ANTHROPIC_API_KEY=sk-ant-...           # set in .env
uv run ai-oip discover "automation pain" --limit 10 --output problems.md
uv run ai-oip workflows --output workflows.md
uv run ai-oip score --output opportunities.md
uv run ai-oip research --output competition.md
uv run ai-oip recommend --output recommendations.md
```

## Architecture

AI-OIP is a **modular monolith**: one repository, one deployment, but
internally split into layers with enforced, one-directional dependencies.
`import-linter` fails CI if a lower layer imports a higher one (see
`pyproject.toml` `[tool.importlinter]` and `docs/architecture/ADR-0002`,
`ADR-0004` for why the layer order looks the way it does).

```
src/ai_oip/
├── runtime/        # composition root + entrypoints (the one module that wires layers)
├── services/       # business logic; the only layer that knows both
│                     agents and repositories
├── collectors/     # external data ingestion
├── evals/          # eval harness — runs prompt golden cases
├── agents/         # single-responsibility AI units (never touch the DB)
├── repositories/   # the ONLY layer allowed to query the database
├── providers/      # LLM vendor clients behind a swappable interface
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
| M0 — Vision & Engineering Foundation | ✅ Complete |
| M1 — Development Environment | ✅ Complete |
| M2 — AI Runtime Foundation | ✅ Complete |
| M3 — Agent Framework & Evaluation Harness | ✅ Complete |
| M4 — Prompt Management | ✅ Complete |
| M5 — Configuration | ✅ Complete |
| M6 — Database Layer | ✅ Complete |
| M7 — Collector Framework | ✅ Complete |
| M8 — Walking Skeleton (Problem Extraction + thin E2E report) | ✅ Complete |
| M9 — Workflow Discovery Agent | ✅ Complete |
| M10 — Opportunity Scoring | ✅ Complete |
| M11 — Competition Research | ✅ Complete |
| M12 — Product Recommendation | ✅ Complete |
| M13 — ICP Generator | Not started |
| M14 — Company Discovery | Not started |
| M15 — Executive Report v2 | Not started |
| MX.1 — Scheduled Runs, Human-in-the-Loop | Not started |
| MX.2 — Human-on-the-Loop (exception review) | Not started |
| MX.3 — Bounded Autonomy (budgets, guardrails, escalation) | Not started |

Execution order is dependency-driven, not strictly numeric (prompts
before agents: M4 → M3 → M7 → M8…M15 → MX.1 → MX.2 → MX.3, staged
autonomy). M8 delivers the first end-to-end output; every later
milestone extends a working pipeline, gated on its eval suite
(ADR-0006). Testing, Docker/CI hardening, and monitoring are
cross-cutting tracks rather than numbered milestones — see
`CLAUDE.md` for details.

> **Note:** the roadmap was renumbered on 2026-07-02. ADRs and older
> commit messages use the previous numbering — the old↔new mapping
> lives in `CLAUDE.md` under "Legacy numbering".

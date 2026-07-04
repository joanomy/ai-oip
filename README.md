# AI-OIP — AI Opportunity Intelligence Platform

**In plain English:** this project reads real complaints people post
online about repetitive, painful work, works out which of those
problems an AI product could realistically fix, checks whether someone
is already building that solution, and hands back a report saying
*build this*, *watch this*, or *skip this* — with the reasoning behind
each call.

### What is it?

An automated research pipeline that finds AI product ideas instead of
someone guessing them. Feed it a topic, and it comes back with a
ranked list of business opportunities, each backed by evidence: real
complaints, a feasibility score, and a check on existing competitors.

### Who is it for?

AI development agencies and consultancies who want a steady stream of
vetted "problems worth solving with AI" instead of guessing what to
build next.

### Why does it exist?

Coming up with a validated AI product idea is slow, manual work: read
forums, guess at pain points, search for competitors by hand, decide
if it's worth building. This automates that legwork so an agency can
skip straight to the decision.

### Which problems does it look at?

Only ones with evidence behind them — real posts from real people
complaining about a task, not hypothetical pain points. Each one gets
scored on how painful it is, how automatable it is, how many people
have it, and whether they'd pay to fix it.

### When do you use it?

Today: on demand, one topic at a time (`ai-oip discover "<query>"`
kicks off a run). Scheduled, recurring reports are a planned future
step, not built yet.

### Where does it get its answers from?

Real posts from Hacker News today (more sources are the next thing
being added), plus a live web search when checking for competitors —
so the competitive check reflects what's true right now, not just
what an AI model happened to learn during training.

### How does it work?

One pipeline, five steps, each feeding the next:

1. **Discover** — collect real problems people post about online.
2. **Find workflows** — group those problems into repeatable tasks an
   AI product could target.
3. **Score** — rate each opportunity on pain, automatability, market
   size, and willingness to pay.
4. **Research competition** — check who's already solving it, using
   live web search so the answer isn't limited to stale AI training
   data.
5. **Recommend** — turn all of that into a build / watch / pass call,
   with reasoning.

Run end to end with one command-line tool:
`ai-oip discover "<query>"` → `ai-oip workflows` → `ai-oip score` →
`ai-oip research` → `ai-oip recommend`.

## Current status

The five-step pipeline above is fully built and working end to end,
including live web search for the competition-research step. Work now
is focused on making the reports good enough to sell — more data
sources beyond Hacker News, a polished report format, and clear
cost-per-report tracking — before any more features get built. See
the status table below for the detailed roadmap.

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

---

Everything below this line is for engineers working on the codebase.

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
| R1 — Web-Grounded Competition Research | ✅ Complete |
| R2 — Collector Breadth (2–3 sources beyond HN) | Not started |
| R3 — Report v2 + Cost Telemetry (the sellable deliverable) | Not started |
| **Sales gate** — 10 design-partner conversations, 3 paid pilots | Blocked on R3 |
| M13 — ICP Generator | Postponed (may land as R3 report content instead) |
| M14 — Company Discovery | Cut |
| M15 — Executive Report v2 | Superseded by R3 |
| MX.1 — Scheduled Runs, Human-in-the-Loop | Postponed |
| MX.2 — Human-on-the-Loop (exception review) | Postponed |
| MX.3 — Bounded Autonomy (budgets, guardrails, escalation) | Postponed |

Execution order (roadmap v4, ADR-0017): **R1 → R2 → R3 → stop building
and sell.** After R3 ships, no further engineering happens until the
sales gate resolves. M8 delivered the first end-to-end output; every
later milestone extends that same working pipeline, gated on its eval
suite (ADR-0006). Testing, Docker/CI hardening, and monitoring are
cross-cutting tracks rather than numbered milestones — see
`CLAUDE.md` for details.

> **Note:** the roadmap was renumbered on 2026-07-02, then reordered
> commercial-first on 2026-07-03 (ADR-0017 — hence "R1/R2/R3" ahead of
> M13+). ADRs and older commit messages use the previous milestone
> numbering; the old↔new mapping lives in `CLAUDE.md` under "Legacy
> numbering".

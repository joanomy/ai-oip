# AI Platform

Production-grade Python platform for autonomously executing AI workflows via
modular, single-responsibility agents.

**Status:** Milestone 0 (Environment & Repo Bootstrap) complete. No business
logic or agents exist yet — this repo currently proves the engineering
toolchain works end-to-end.

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
uv run pytest                    # test with coverage
uv run pre-commit run --all-files  # run all hooks manually
```

## Project Status & Roadmap

See `docs/architecture/` for Architecture Decision Records (ADRs) explaining
*why* each engineering decision was made, not just what it is.

Milestones are executed one at a time: Architecture → Implementation →
Testing → Documentation → Review → Approval. Nothing is skipped.

| Milestone | Status |
|---|---|
| M0 — Environment & Repo Bootstrap | ✅ Complete |
| M1 — Project Architecture & Folder Structure | ⏳ Next |
| M2 — Configuration Management | Not started |
| M3 — Logging & Observability | Not started |
| M4 — Database Layer | Not started |
| M5 — Prompt Management | Not started |
| M6 — Agent Framework Core | Not started |
| M7 — Inter-Module Communication | Not started |
| M8 — Testing Framework | Not started |
| M9 — Dockerization | Not started |
| M10 — CI/CD Readiness | Not started |
| M11 — Monitoring & Health Checks | Not started |
| M12 — Documentation System | Ongoing |

# ADR-0001: Bootstrap Tooling Choices

**Status:** Accepted
**Date:** 2026-07-01
**Milestone:** M0 — Environment & Repo Bootstrap

## Context
Before any business logic or agent code is written, the project needs a
tooling baseline: dependency management, linting, type checking, testing,
and CI. These decisions are expensive to reverse once the codebase grows,
so they're made deliberately and recorded here.

## Decisions

| Concern | Choice | Alternative considered | Why not the alternative |
|---|---|---|---|
| Dependency management | uv | Poetry | Poetry is mature but 10-100x slower on install/resolve; uv's lockfile and Python-version management cover the same ground with less overhead. |
| Lint + format | ruff | flake8 + black + isort | Three tools, three configs, slower. Ruff replaces all three with one fast binary and one config block. |
| Type checking | mypy (strict mode) | pyright | Pyright is faster, but mypy has more mature CI/plugin ecosystem and is the more common choice for teams that will grow beyond one engineer. |
| Test runner | pytest + pytest-asyncio | unittest | pytest's fixture system and async support are essential once agents (async LLM I/O) are introduced in M6. |
| Pre-commit hooks | pre-commit framework | CI-only enforcement | Catching issues before commit is cheaper than catching them in CI — faster feedback loop. |

## Consequences
- All future code must pass `ruff check`, `ruff format --check`, and
  `mypy --strict` before merge. This is enforced in CI, not optional.
- Coverage threshold starts at 80% (see `pyproject.toml` / CI config) —
  deliberately not 100%, to avoid low-value tests early. Revisit as the
  codebase matures.
- `strict = true` in mypy means every new module must have full type
  annotations from the start. This is intentionally strict from day one —
  loosening a strict baseline is easy; tightening a loose one later is not.

## Revisit When
- Team grows beyond 1-2 engineers (revisit mypy vs pyright for editor
  performance).
- Coverage threshold should ratchet upward as core modules stabilize.

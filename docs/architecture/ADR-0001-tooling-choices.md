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

## Addendum (2026-07-02, during M1)
Original `.pre-commit-config.yaml` used the standard `ruff-pre-commit` and
`mirrors-mypy` hook repos with pinned revisions. This caused real version
drift: those pinned versions lagged behind the `uv`-managed versions used
in CI and local dev, producing false failures (an old ruff flagging a rule
removed upstream; an old mypy rejecting PEP 695 generic syntax that our
target Python version and current mypy both support).

Fixed by switching pre-commit to `language: system` hooks that invoke
`uv run ruff`/`uv run mypy`/`uv run lint-imports` directly — the exact
same binaries CI and local dev use. Trade-off: contributors must run
`uv sync` before `pre-commit run` works (acceptable; `uv sync` is already
step one of onboarding).

## Addendum 2 (2026-07-02, post-M4 engineering review)

Coverage threshold ratcheted 80% → 90%, per this ADR's own "Revisit
When" — the foundation modules are stable at 100%, and an 80% floor
would let the first business-logic milestones (M5/M6) land with a large
untested surface while CI stayed green. Deliberately not 100%: that
invites low-value tests for trivial branches, which the original
decision explicitly warned against.

At the same time, the floor moved from repeated `--cov-fail-under` CLI
flags (CI + docs) into `pyproject.toml` `addopts` — one source of
truth, same drift-prevention reasoning as the pre-commit fix above.

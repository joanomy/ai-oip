# ADR-0009: Collector Framework & Infrastructure Track

**Status:** Accepted
**Date:** 2026-07-02
**Milestone:** M7 — Collector Framework (+ the Docker/CI/Postgres
cross-cutting track ADR-0006 recommended landing alongside it)

## Context

The last platform milestone before business work begins. Two halves:
the collector layer (external raw signal in, typed schemas out), and
the infrastructure hardening that must exist before the platform talks
to real external services — Docker, CI Postgres, real-database
integration tests (closing ADR-0005's SQLite-only trade-off).

## Decisions

### 1. `BaseCollector`: fetch and normalize, nothing more

`collect(query, limit) -> list[CollectedItem]`, raising
`CollectorError` on any failure — vendor exceptions never escape, the
same contract shape as `LLMProvider`. Collectors never persist
(services own that) and never interpret (agents own that). No
`CollectorQuery` schema yet — a string query satisfies the current
requirement; a richer query object appears when a second source
genuinely needs one.

Retry/rate-limit machinery is deliberately absent: collectors run
manually until MX.1 (scheduled runs), and retry policy belongs to the
scheduler that owns the cadence, not inside each collector. Timeouts
exist (30s default on the HTTP client); failures surface as
`CollectorError` for the caller to decide.

### 2. `CollectedItem`: one normalized schema across all sources

The first real data-in-motion schema. Source-specific extras go in
`metadata` rather than growing per-source fields — the Problem
Extraction agent should consume one shape regardless of where signal
came from.

### 3. First source: Hacker News (Algolia HN Search API)

Chosen over Reddit/app-store reviews/job boards for the walking
skeleton because the API is **keyless** — no OAuth, no secrets, works
unmodified in CI and local dev — while "Ask HN" discussion is dense
with people describing real workflow pain, exactly the Problem
Extraction agent's raw material. Reddit is the natural second
collector, when its OAuth cost buys genuinely new signal. The HTTP
client is injectable (the `AnthropicProvider` pattern); hits are
validated through a pydantic model, so malformed API payloads fail as
`CollectorError`, not deep in an agent.

### 4. Real-Postgres integration tests, env-gated

`tests/integration/` runs the repository layer against actual Postgres
— including what SQLite structurally cannot verify (server-side
`func.now()` timestamptz behavior, real asyncpg driver, real dialect).
Gated on `INTEGRATION_DATABASE_URL`: CI sets it (Postgres 16 service
container) so integration always runs there; locally it's opt-in via
`docker compose up postgres`, and unset means *skip*, never fail — the
local quality gate must not require Docker. The gate variable is read
directly (narrow ruff TID251 exemption for `tests/integration/`)
because "unset means skip" is the opposite of Settings' fail-fast
contract.

### 5. Docker: uv-layered runtime image, honest placeholder CMD

Dependencies install from the lockfile in their own cacheable layer;
non-root user; no fake entrypoint — the CMD is an import smoke check
until the walking skeleton adds the first real one, and CI builds and
runs the image so it can't silently rot. docker-compose provides the
local Postgres (and an `app` build target).

### 6. Composition root: lands at M8

Collectors don't touch the database, so M7 still doesn't force the
deferred decision (ADR-0002 addendum, ADR-0008 §9). The walking
skeleton is the first component composing collector + agent +
repository + provider — the decision is due there, and this is the
last deferral available.

## Consequences

- ADR-0005's "SQLite-only" known trade-off is **closed**: every CI run
  now exercises real Postgres.
- New runtime dependency: `httpx` (already present transitively via
  the anthropic SDK; now explicit because we import it).
- CI gained a second job (image build + smoke run). The quality gate's
  five local commands are unchanged and still Docker-free.
- M8 has everything it needs: collector (signal), prompt format,
  provider, agent framework, eval harness, real database, runtime
  image.

## Revisit When

- MX.1 (scheduled runs): add retry/backoff policy at the scheduler
  level; revisit whether collectors need incremental/cursor collection
  (`since` parameters) rather than query-limit snapshots.
- A second collector lands: extract shared HTTP/retry helpers only if
  real duplication appears — not before.
- Alembic gains its first real migration (M8, when the first business
  table exists): wire `alembic upgrade head` into compose/CI startup.

# ADR-0004: Structured Logging and the Config → Logging Dependency

**Status:** Accepted
**Date:** 2026-07-02
**Milestone:** M3 — Logging & Observability Foundation

## Context
Structured (queryable) logging needs to exist before agents and
pipelines are built, or every log call gets retrofitted later. It also
needs to know the deployment environment and desired verbosity — both
of which live in `Settings` (M2) — to decide how to render output.

## Decisions

### 1. `structlog`, configured once via `configure_logging(settings)`
No module configures logging itself. One function, called once at
process startup, driven by `Settings`. Every other module calls
`get_logger(__name__)` and never touches `structlog.configure` or the
stdlib `logging` module directly.

### 2. Environment-driven rendering
- `development` → `structlog.dev.ConsoleRenderer` (colorized, human-readable)
- `staging` / `production` → `structlog.processors.JSONRenderer` (single-line JSON, safe for a log aggregator to parse and query on structured fields)

Demonstrated directly during this milestone — see M3 conversation
record for side-by-side output of both modes.

### 3. Level filtering via `structlog.make_filtering_bound_logger`,
driven by `Settings.log_level`. A log call below the configured
threshold is dropped before any processor runs — verified by test
(`test_log_level_filtering_drops_below_threshold_messages`).

### 4. Architecture change: `logging`/`monitoring` now depend on `config`
**This revises the layer contract from ADR-0002/ADR-0003.** Originally
`config`, `logging`, and `monitoring` were sibling foundation layers,
none depending on each other. That was wrong the moment logging needed
to read `Settings.log_level` — a real, justified dependency, not scope
creep. New order:

```
logging | monitoring
        ↓
      config
        ↓
       core
```

`config` still depends on nothing but `core` — it remains the most
foundational layer other than `core` itself, it's just no longer a
sibling of `logging`. Verified both directions during this milestone:
`logging → config` is now allowed; a deliberately-introduced
`config → logging` import was confirmed still rejected by
`import-linter`.

### 5. `reset_logging()` exists only for test isolation
Production code never calls it. Tests call it before and after
`configure_logging()` to prevent one test's logging configuration
(level, renderer) from leaking into the next.

## Consequences
- Any module that will eventually log (which is nearly everything)
  gets `get_logger(__name__)`, not `import logging`.
- The layer contract will likely need one more revision when `agents/`
  (M6) needs to log — `agents` is already above `logging` in the
  hierarchy so this should be a non-event, but worth checking against
  the actual contract at that milestone rather than assuming.
- `structlog.get_logger()` returns `Any` at the type level; wrapped
  with an explicit `cast` to `FilteringBoundLogger` in `get_logger()`
  so callers get real type checking rather than the cast propagating
  outward.

## Revisit When
- Multiple processes/services need correlated logs (e.g., a pipeline
  run ID threading through several log calls) — `structlog.contextvars`
  is already in the processor chain (`merge_contextvars`) specifically
  so this can be added later via `structlog.contextvars.bind_contextvars`
  without changing the configuration shape. Not wired up yet — no
  pipeline exists to correlate (M7).
- Log volume in production justifies sampling or async log shipping —
  not a concern at current scale.

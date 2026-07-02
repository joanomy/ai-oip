# ADR-0011: Workflow Discovery

**Status:** Accepted
**Date:** 2026-07-02
**Milestone:** M9 — Workflow Discovery Agent

## Context

Second business milestone, first to *extend the working pipeline*: it
consumes what M8 persists (problems) and produces the next stage's
input (workflows). Largely a stamp of the M8 recipe; the decisions
below are what's new.

## Decisions

### 1. Workflow→problem linkage is a JSON id list, not a join table

`WorkflowRecord.problem_ids` stores problem UUIDs as a JSON array.
Nothing queries "workflows for problem X" yet — the read paths are
"list workflows" and "count links". A normalized association table
(and its async relationship-loading complexity) is deferred until a
milestone actually needs the relational query; the migration cost then
is one table plus a backfill from the JSON column.

### 2. Repository read paths return schemas

`ProblemRepository.list_details()` returns `ProblemDetail` (data in
motion), completing the pattern ADR-0010 started on the write path:
the ORM never crosses the repository boundary in either direction.
Services now compose entirely over schemas.

### 3. No `collected_items` table (ADR-0010's open question, answered no)

Workflow discovery consumes *problems*, not raw signal. The
denormalized source columns on `problems` remain sufficient. Raw-item
storage waits for a milestone that re-reads raw text.

### 4. Index-based linkage with the same degradation stance

The agent returns 1-based `problem_indexes`; out-of-range indexes are
dropped (the workflow is still stored and reported) — consistent with
M8's source_index handling: an imperfect linkage never costs the
discovery itself.

### 5. One entrypoint per pipeline stage, consolidation deferred

`ai-oip-workflows` joins `ai-oip-skeleton` as a second console script.
By M10–M11 there will be enough stages to justify one `ai-oip` CLI
with subcommands; consolidating then is a rename, not a redesign.

## Consequences

- The pipeline is now two stages deep with a persisted handoff:
  problems (M8) → workflows (M9). M10 (Opportunity Scoring) reads
  workflows the same way M9 reads problems.
- Migration `0002` (workflows) is applied to real Postgres by CI's
  existing alembic step — the pattern scales with zero CI changes.

## Revisit When

- A milestone needs "workflows for problem X" or joins across the
  linkage: introduce the association table then.
- M10 design: scoring likely wants `WorkflowRepository.list_details()`
  — stamp the schema-returning read pattern.
- 3+ console scripts exist: consolidate into one `ai-oip` CLI.

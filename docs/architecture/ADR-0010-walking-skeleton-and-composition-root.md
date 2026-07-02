# ADR-0010: Walking Skeleton & the Composition Root

**Status:** Accepted
**Date:** 2026-07-02
**Milestone:** M8 — Walking Skeleton (Problem Extraction + thin E2E report)

## Context

The first business milestone: one human-triggered end-to-end slice —
collect (Hacker News) → extract problems (first concrete agent) →
persist (first business table) → markdown report. It also forces the
decision deferred since ADR-0002: who composes the layers.

## Decisions

### 1. The composition root is `runtime/` — a named, documented exception

New top-level package at the very top of the layer stack. It alone
creates engines/session factories, opens unit-of-work scopes, and
wires collector + agent + provider + repository into services. It is
deliberately absent from the "only repositories access the database
layer" contract sources — the one sanctioned exception, recorded in
the pyproject contract comment and here. This resolves ADR-0002's
open question via option (a) (named exception) rather than option (b)
(moving session management out of `models/`) — session code stays
where it is, and the exception is enforced-by-omission plus documented
intent. Nothing else follows this precedent.

Corollary discovered in implementation: the forbidden contract now
sets `allow_indirect_imports = true`. Once services import
repositories that import models, the *chain* services → repositories →
models exists by design — the contract's job is to stop **direct** ORM
/ session access, and as originally written it also banned the
legitimate indirection. First real service code surfaced this.

### 2. The ORM never crosses the repository boundary upward

Services cannot construct `ProblemRecord` (models are forbidden to
them), so `ProblemRepository.add_extracted()` accepts *schemas*
(`ExtractedProblem`, `CollectedItem`) and builds the ORM record
inside. Repositories translate data-in-motion into data-at-rest; that
is now the standing pattern for every future entity.

### 3. One batched completion per run, with `source_index` provenance

All collected items go into a single prompt as a numbered digest
(items truncated at 1,500 chars); the prompt requires a `source_index`
per extracted problem so attribution survives batching. An
out-of-range index degrades to collector-level attribution rather than
failing the run — a slightly wrong index is not worth losing the
extraction. Per-item calls (better isolation, more cost) become
worthwhile only with evidence batching hurts extraction quality.

### 4. First production prompt: `extract_problems` v1

Follows the full M4 contract (frontmatter, versioning, eval fixtures).
Groundedness rules are explicit (never invent; evidence quotes the
source; empty list when nothing is described). The agent uses the
prompt's `role` field as the system prompt — metadata drives the
request, not code. Lesson recorded: YAML frontmatter treats `{...}`
in plain scalars as flow syntax — rules containing JSON must be
quoted.

### 5. Problems are stored denormalized; no raw-items table yet

`problems` carries its own source attribution columns. A normalized
`collected_items` table appears when a milestone actually needs to
re-read raw signal (likely Workflow Discovery), not speculatively.

### 6. First migration is hand-written; CI applies it against real Postgres

Autogenerate needs a live database, which local dev deliberately
doesn't require. The migration mirrors `ProblemRecord`, and the new CI
step (`alembic upgrade head` against the service container) is the
parity check that matters — a drifted migration fails the build.

### 7. Eval fixtures run in CI against a fake provider

`prompt_completion_target(prompt, provider)` renders each golden case
and completes it; CI wires a fake provider (verifying the whole
harness path: fixtures load → render → complete → evaluate), and the
identical target runs against the live model manually. Live-model
evals in CI wait until there's an API-key budget decision.

## Consequences

- The recipe for every M9–M15 agent is now demonstrated end to end:
  prompt dir + schemas + agent class + repository method + service
  wiring + eval fixtures.
- `ai-oip-skeleton "<query>"` (console script) is the platform's first
  runnable product surface. Prerequisites: migrated DB, API key.
- `runtime/` is where MX.1's scheduler will live — the skeleton's
  manual trigger is the seam autonomy gets added around.

## Revisit When

- M9 (Workflow Discovery): decide whether it reads persisted problems
  (likely) — that's when a `collected_items` table and richer
  repository queries earn their place.
- Extraction quality data exists: revisit batched-vs-per-item calls
  and prompt v2 with real eval results.
- API-key budget for CI: enable live-model eval runs on a cadence.

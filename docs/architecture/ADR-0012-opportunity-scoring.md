# ADR-0012: Opportunity Scoring

**Status:** Accepted
**Date:** 2026-07-02
**Milestone:** M10 — Opportunity Scoring

## Context

Third pipeline stage, and the first agent whose output is a *judgment*
rather than an extraction. The central design question: where does the
scoring arithmetic live?

## Decisions

### 1. The LLM judges, the code computes

The agent scores five dimensions (1-10, each with a grounding
rationale); the prompt explicitly forbids totals and rankings. The
weighted 10-100 total is deterministic arithmetic in
`services/opportunity_scoring.py::weighted_total`. Consequences of
this split: weights can be tuned without touching a prompt (no eval
re-run needed for a weight change), totals are reproducible and
testable, and the model can't quietly apply its own weighting.

### 2. The rubric (CEO-approved starting point)

pain_intensity 0.25, automation_feasibility 0.25, frequency 0.20,
market_breadth 0.20, willingness_to_pay 0.10. Weights are a
constructor argument (`DEFAULT_WEIGHTS` as default) — a business rule
owned by composition, revisable without code archaeology. Externalize
to Settings only when someone actually needs per-deployment tuning.

### 3. Dimensions are a fixed, typed set

`WorkflowScore` declares five required `DimensionScore` fields — not a
free-form dict. A missing, extra, or misspelled dimension fails at the
output guardrail instead of silently skewing totals. Adding a
dimension is deliberately a schema + prompt + weights change.

### 4. Invalid workflow_index drops the score entirely

Unlike M8/M9 (where the artifact is kept with degraded attribution), a
judgment with no workflow to attach to is meaningless — skipped, not
stored.

### 5. CLI consolidation (ADR-0011's note, come due)

Third stage = third entrypoint = the unified `ai-oip` CLI:
`ai-oip discover "<query>"` / `ai-oip workflows` / `ai-oip score`.
Legacy per-stage scripts remain as aliases; new stages get subcommands
only.

## Consequences

- Pipeline: problems → workflows → ranked opportunities
  (`opportunity_scores`, migration 0003 — CI applies it unchanged).
- M11 (Competition Research) consumes the top-ranked opportunities the
  same way each stage reads its predecessor.

## Revisit When

- Real scoring data exists: calibrate the rubric (weights AND prompt
  anchors) against human judgment on actual scored workflows.
- Per-deployment weight tuning is requested: move weights to Settings.
- Score history matters (re-scoring the same workflow over time):
  add a run/batch identifier to `opportunity_scores`.

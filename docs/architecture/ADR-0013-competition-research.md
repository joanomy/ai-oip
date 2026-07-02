# ADR-0013: Competition Research

**Status:** Accepted
**Date:** 2026-07-02
**Milestone:** M11 — Competition Research

## Context

Fourth pipeline stage, and the first whose quality depends on
knowledge of the outside world. The CEO decision: how does the agent
know who else solves a workflow?

## Decisions

### 1. Model knowledge only (v1), web search as v2 — CEO-selected option

The agent assesses landscapes from training knowledge. Chosen because
it ships with zero new infrastructure, competition in established
workflow categories moves slowly, and the upgrade path is clean: when
live data proves necessary, `LLMProvider` grows tool support
(web search) and the prompt gets a v2 — the interface, schemas, and
storage don't change. The v2 trigger is *evidence* (stale assessments
observed on real runs), not speculation.

### 2. Honesty constraints are load-bearing prompt content

The prompt forbids inventing competitors, forbids stale specifics
(pricing/funding/launch dates), and declares "empty competitors +
saturation low" a valid answer — because a knowledge-cutoff model
asked about niches WILL confabulate without these. A test pins the
"NEVER invent" rule so a prompt edit can't silently drop it. The
markdown report always carries a knowledge-lag banner — the honesty
lives in the deterministic layer too, not just the model's
instructions.

### 3. `saturation` is a Literal enum

"low" | "medium" | "high" at the schema level — a fourth value fails
the guardrail rather than entering the database as free text.

### 4. First two-store read, with dedupe

Targets = top opportunity scores joined to workflow details.
Re-scored workflows dedupe to their best score (over-fetch 3x then
filter); dangling workflow_ids are skipped. This is the shape every
downstream stage (M12+) will reuse when reading ranked upstream data.

## Consequences

- Pipeline: problems → workflows → ranked opportunities → competitive
  landscapes (`competition_assessments`, migration 0004).
- `ai-oip research` subcommand; per ADR-0012, no new standalone script.
- M12 (Product Recommendation) has everything it needs: a scored,
  competition-assessed opportunity is exactly the input a
  recommendation agent wants.

## Revisit When

- Real runs show stale/wrong competitor data: implement v2 (provider
  tool support + prompt v2). This is the expected eventual outcome —
  budget for it around MX.
- The dedupe/join pattern appears a third time: extract a shared
  read-helper, not before.

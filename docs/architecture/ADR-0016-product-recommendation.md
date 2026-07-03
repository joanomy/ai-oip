# ADR-0016: Product Recommendation

**Status:** Accepted
**Date:** 2026-07-03
**Milestone:** M12 — Product Recommendation

## Context

Fifth pipeline stage. ADR-0013 anticipated this exactly: "a scored,
competition-assessed opportunity is exactly the input a recommendation
agent wants." The question was what to do with an opportunity that
has a score but no competitive assessment yet.

## Decisions

### 1. Three-store read, gated on research — not just scored

Targets require a score, a workflow detail, *and* a competition
assessment. A scored-but-unresearched workflow is skipped, not
failed — a recommendation without a competitive landscape is a guess,
not a judgment, and this pipeline's discipline (ADR-0012, ADR-0013) is
to drop inputs that can't support a real judgment rather than let the
agent fabricate context. `CompetitionRepository.get_latest_by_workflow`
takes the most recent assessment per workflow (freshest beats highest,
since there's no score to rank competition by) — mirrors
`OpportunityRepository.list_top`'s "best wins" dedupe for scores.

This is the join-dedup pattern's **second** occurrence (competition
research was the first, ADR-0013 §4). Per ADR-0014's revised trigger
(reassessing ADR-0013's original "third time" call), a shared
read-helper is still deferred — extract only if a third occurrence
appears.

### 2. Honesty analog: forced variety, not forced positivity

Competition research's load-bearing constraint was "never invent."
Here the equivalent risk is different: an agent asked to recommend
will default to recommending — "build" for everything, which is
useless for a studio trying to prioritize. The prompt explicitly
forbids that ("Do not recommend 'build' for every opportunity —
reserve it for a genuine, differentiated gap") and is pinned by test,
same pattern as ADR-0013's "NEVER invent" pin.

### 3. `recommendation` is a Literal enum

`"build" | "watch" | "pass"`, same guardrail pattern as `saturation`
(ADR-0013 §3) — a fourth value fails validation rather than entering
the database as free text.

### 4. MVP scope grounded in the workflow's own steps

The digest surfaces the workflow's `steps` and the prompt instructs
`mvp_scope` to automate those steps specifically, not offer generic
product advice — keeps the recommendation falsifiable against the
same workflow record a human would read.

## Consequences

- Pipeline: problems → workflows → ranked opportunities → competitive
  landscapes → build/watch/pass plans (`product_recommendations`,
  migration 0005). `ai-oip recommend` subcommand.
- `CompetitionRepository` gained a second read method
  (`get_latest_by_workflow`), following the platform/domain seam
  (ADR-0015): the method lives on the domain repository, not a
  platform frame, so contract #4 required no new source-side entries —
  only the four new domain modules added to the forbidden list.

## Revisit When

- The join-dedup-across-three-stores pattern appears again (M13+):
  extract the shared read-helper this time.
- Real runs show the agent still defaults to "build" despite the
  constraint: strengthen the prompt or add a distribution check in
  the service layer before persisting.

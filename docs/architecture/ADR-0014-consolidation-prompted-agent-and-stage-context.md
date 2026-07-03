# ADR-0014: Consolidation — PromptedAgent & the Stage-Context Frame

**Status:** Accepted
**Date:** 2026-07-03
**Milestone:** Post-M11 architecture review remediation (pre-M12)

## Context

M8–M11 stamped four pipeline stages from one recipe. The post-M11
review found the two frames that stamping had duplicated four times
each: the agent's render→complete→parse shape, and the runtime
stage-composition lifecycle. With M12–M14 about to make both ×7, the
review approved consolidating now (findings A and B; C and D —
repository read helpers and digest formatting — were assessed and
deliberately deferred as not worth their abstraction cost yet).

## Decisions

### 1. `PromptedAgent` (agents/base/prompted.py)

Owns digest → render → complete(system=role) → guardrail-parse once.
A concrete agent is now: `name`, `digest_variable`, `output_schema`,
and a `digest()` method. **Convenience, not contract**: `BaseAgent`
remains the interface, so a future agent that doesn't fit the
single-completion shape (multi-turn, tool-using — e.g. competition
research v2 with web search) implements `BaseAgent` directly and
skips the helper. This is also now the single attachment point for
cross-cutting agent behavior (retries, token-usage logging) when a
milestone needs it.

### 2. `stage_context` (runtime/composition.py)

Owns the stage lifecycle once: Settings/engine/provider/prompt-loader
resolution (production defaults unless overridden — the same test
seams as before), one unit-of-work session, engine disposal only when
the context created the engine. Stage modules contribute only agent +
repositories + service wiring. One deliberate improvement over the
copied original: an owned engine is now disposed even when provider
resolution fails (previously it leaked on that path). This is also
where MX.1's scheduling hooks will attach.

## Consequences

- Each stage module and agent shrank by roughly half; M12–M14 stamp
  the consolidated pattern.
- Zero public-signature changes: all 156 tests pass unmodified — the
  refactor's correctness proof.

## Revisit When

- A new agent doesn't fit PromptedAgent: implement BaseAgent directly;
  if that happens twice, reassess the frame rather than forcing it.
- Findings C/D re-trigger: repository read-path or digest duplication
  reaching ×6 justifies revisiting the deferred extractions.

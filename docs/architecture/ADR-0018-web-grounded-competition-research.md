# ADR-0018: Web-Grounded Competition Research (R1)

**Status:** Accepted
**Date:** 2026-07-03
**Milestone:** R1 — Web-Grounded Competition Research (roadmap v4,
ADR-0017)

## Context

ADR-0013 shipped competition research model-knowledge-only (v1) and
named its own upgrade path: "when live data proves necessary,
`LLMProvider` grows tool support (web search) and the prompt gets a
v2 — the interface, schemas, and storage don't change." ADR-0017
declared that trigger fired on commercial grounds — a customer paying
for competitive intelligence will observe staleness in the first ten
minutes, which a knowledge-lag disclaimer cannot fix for a paid
product. R1 is that upgrade, exactly as ADR-0013 scoped it.

## Decisions

### 1. Grounding is a provider-seam capability, not an agent-specific hack

`LLMProvider.CompletionRequest` gains an optional `web_search:
WebSearchOptions | None` field (`max_uses`, `allowed_domains`);
`CompletionResponse` gains `sources: tuple[str, ...]`. Both are
provider-agnostic — no Anthropic SDK types cross the `providers/`
boundary. `AnthropicProvider` maps this to the server-side
`web_search_20260209` tool: search runs entirely on Anthropic's
infrastructure and returns in the same response, so no client-side
tool loop was built. Any future provider implements the same two
fields however its vendor grounds a completion.

### 2. Two vendor mechanics stay inside `providers/`

- **`pause_turn` continuation.** The server-side tool loop can pause
  mid-turn; the provider re-sends with the paused assistant turn
  echoed back unchanged, bounded by `_MAX_PAUSE_CONTINUATIONS` (5) so
  a stuck loop fails loudly (`ProviderError`) instead of spending
  silently forever.
- **Source extraction.** URLs are read from `web_search_tool_result`
  blocks by code, deduplicated, and never taken from model-generated
  text — provenance is a fact the tool call returns, not a claim the
  model could be asked to report (and therefore could fabricate).
  An error-shaped result block (e.g. `max_uses_exceeded`) yields no
  sources rather than failing the completion.

### 3. `PromptedAgent` grows a `run_detailed()` widening, not a second frame

Callers that need response metadata (sources here; token usage for
R3's cost telemetry next) call `run_detailed()` for `(output,
CompletionResponse)`; `run()` is unchanged and still returns just the
parsed output. A new `build_request()` hook lets a concrete agent
attach provider options — `CompetitionResearchAgent` overrides it to
attach `web_search` — without every agent re-implementing the
digest → render → complete → parse frame.

### 4. Sources are batch-level, not per-competitor

One completion covers every target in a research batch (the existing
digest shape from ADR-0013 §4). The model cannot honestly attribute a
source to one specific competitor claim within that batch, so
`CompetitionResearchService` attaches the same source list to every
assessment persisted from that run — labelled as sources consulted
during the run, not sources specific to that workflow. Per-competitor
evidence citations are left to R3 if the report format calls for them.

### 5. Grounded is the default; ungrounded stays one parameter away

`run_competition_research(..., grounded: bool = True)`. Production
runs are grounded by default — R1's whole point. The v1 (ADR-0013)
model-knowledge-only path is not deleted: `grounded=False` constructs
the same agent with `web_search=None`, useful for cost-constrained or
offline scenarios. `web_search_max_uses` (default from
`Settings.competition_research_web_search_max_uses`, the cost knob,
externalized per CLAUDE.md's config-is-for-values rule) overrides the
per-run search bound.

### 6. Storage: additive, nullable `sources` column

Migration 0006 adds `competition_assessments.sources` (nullable JSON).
`None` means "this assessment was never grounded" (v1 rows, or an R1
run with `grounded=False`); an empty list means "grounded, but search
found nothing" — the two stay distinguishable in stored data, which
matters for the honesty discipline (an empty list should read as "we
looked and found nothing," not "we didn't look").

### 7. Two banners, one honesty discipline

`CompetitionReport.grounded` (default `False`) drives which banner
`render_competition_report` shows: the v1 knowledge-lag disclaimer, or
a grounded banner naming the distinct source count and still telling
the reader to verify critical claims independently — grounding reduces
staleness, it does not eliminate the need to verify (ADR-0013's
honesty-is-load-bearing discipline carries forward unchanged).

### 8. Prompt v2, honesty constraints carried forward and extended

`research_competition/v2.md` keeps every ADR-0013 constraint verbatim
("NEVER invent" is pinned by test, same as v1) and adds: search first,
cite only what search actually surfaced, and treat a thin/empty search
result as an honest answer rather than a gap to fill from training
knowledge. `v1.md` is retained on disk and stays loadable by explicit
version number — prompt version history is retained, diffable
(ADR-0007) — even though `PromptLoader.load("research_competition")`
now resolves to v2 by default.

## Consequences

- `ai-oip research` is grounded by default; CLI surface (`--limit`,
  `--output`) is unchanged — grounding is a runtime/config concern,
  not a new flag, keeping the milestone scoped per ADR-0017 (no
  browsing agent, no multi-turn research loops, no per-competitor deep
  dives).
- `CompetitionResearchService.research()` now calls
  `agent.run_detailed()` and reads `agent.grounded` to decide whether
  to persist sources — the three-store read and dedupe logic from
  ADR-0013 §4 is untouched.
- Per-run search-count and token-usage data now exists in
  `CompletionResponse.usage`/`sources` at every call site — the raw
  material R3's cost-per-report telemetry needs, logged from day one
  per the R1 milestone's risk mitigation.

## Revisit When

- Live runs show `_MAX_PAUSE_CONTINUATIONS` (5) is too tight or too
  loose for real search-heavy assessments — tune from observed data,
  not speculation.
- R3 wants per-competitor evidence citations: revisit the batch-level
  sources decision (§4) then, with real report-design requirements in
  hand, rather than guessing now.
- Real runs show grounded assessments are still stale or thin despite
  search: that is evidence for tightening `allowed_domains` or raising
  `max_uses`, not for a new grounding mechanism.

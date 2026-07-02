# ADR-0008: Agent Framework & Evaluation Harness

**Status:** Accepted
**Date:** 2026-07-02
**Milestone:** M3 — Agent Framework & Evaluation Harness

## Context

The BaseAgent interface has existed since the architecture milestone;
this milestone builds the machinery around it: how agents reach models,
how they're looked up, how their output is validated, how runs are
observed, and how their quality is measured. Prompts (M4) landed first
— deliberately — so the eval harness had a fixture contract
(`PromptEvalCase`, ADR-0007) to build against.

Design defaults confirmed with the CEO before execution: agents group
by business domain (not by provider); "multi-provider" means multiple
AI model providers; no multi-tenancy plumbing yet.

## Decisions

### 1. `LLMProvider` interface; vendor SDKs never escape `providers/`

`CompletionRequest` in, `CompletionResponse` out, `ProviderError` on
failure — that is the whole contract. Agents receive a provider by
constructor injection and never import a vendor SDK, which is what
makes "replace the AI provider with minimal code change" (CLAUDE.md)
literally one new class. Deliberately minimal: no tool use, streaming,
or structured-output support until a concrete agent needs them.

`CompletionRequest` has no sampling parameters — current Anthropic
models reject temperature/top_p, and prompting is the supported
steering mechanism. Adaptive thinking is on by default (current
provider guidance); the default model (`claude-opus-4-8`) lives in
`Settings.anthropic_model`, overridable per request.

### 2. `AnthropicProvider` with an injectable client

Tests inject a fake client and verify the request/response mapping
(system omission, thinking config, text-block extraction, token usage)
without network or key. Production construction goes through
`anthropic_provider_from_settings`.

### 3. First secret: `SecretStr`, optional globally, required at the seam

`Settings.anthropic_api_key` is `SecretStr | None` — masked in
repr/logs (the pattern ADR-0003 earmarked for this milestone). It is
deliberately *not* required by Settings validation: environments that
run no agents need no key. The fail-fast moment is provider
construction, which raises `ConfigurationError` — still startup, not
first-API-call. An empty `ANTHROPIC_API_KEY=` is normalized to None so
a blank .env line can't produce a present-but-empty secret. A dedicated
secrets manager remains deferred to the Docker/CI track (per ADR-0003's
revisit clause: env vars suffice until deployment).

### 4. Agent registry: instance, not singleton

`AgentRegistry` maps `BaseAgent.name` to the class, fulfilling the
registry promise in BaseAgent's docstring. The composition root
instantiates one and registers the deployment's agents — no global
mutable state. Registration/lookup mistakes raise ValueError/KeyError
(programmer errors, explode at startup), not AIOIPError (reserved for
runtime categories pipelines catch).

### 5. Output guardrail: `parse_json_output`

The bridge between raw model text and the "typed output out" contract:
tolerates a markdown fence (common model behavior) and nothing looser —
prose around JSON fails as `AgentExecutionError` rather than being
salvaged by heuristics that would mask a misbehaving prompt.

### 6. Run tracing: `log_agent_run`

One context manager emitting structured `agent_run_started` /
`agent_run_completed` / `agent_run_failed` events with duration —
queryable by agent name, the observability seed for the MX stages.
Token/cost logging happens at call sites from
`CompletionResponse.usage` (one run may make several provider calls).

### 7. Eval semantics: `contains` / `not_contains` / `matches`

The runner defines what ADR-0007 left loose. Three deterministic
string checks; a case may combine them; unknown keys or non-string
values raise `EvalError` (a mistyped fixture must fail loudly, not
pass as an empty check). A failing case is a *result* in the
`EvalReport`, never an exception. LLM-as-judge is deliberately absent
— add it only if property checks prove insufficient on real agents
(ADR-0006's revisit clause).

The runner evaluates `(variables) -> awaitable str`, not `BaseAgent` —
it needs no knowledge of any agent's input schema; the adapter from
agent to callable lives with the agent.

### 8. Layer placement, enforced

Two new top-level packages, added to the import-linter layers list in
the same change (the manual-update hazard CLAUDE.md flags for exactly
this milestone): `evals` sits beside `collectors` (may import agents,
prompts); `providers` sits beside `repositories` (may import config,
core). Both are added to the "Only repositories access the database
layer" forbidden contract.

### 9. Composition root: still deferred, now to M7/M8

ADR-0002's addendum deferred "who creates DB sessions" to this
milestone. Nothing in M3 touches the database, so deciding now would
be speculation. The first component that composes providers + agents +
repositories together (the collector pipeline at M7, or the walking
skeleton at M8) forces the decision; it should be made there, not
implicitly.

## Consequences

- A concrete agent is now: a prompt directory (M4 format), a class
  implementing BaseAgent with an injected provider, `parse_json_output`
  on its output, registration by name, and passing eval fixtures. That
  recipe is what M8–M15 stamp out.
- New runtime dependency: `anthropic` (async SDK).
- `ProviderError` vs `AgentExecutionError` gives pipelines the
  retryable/not-retryable distinction at the exception-category level.

## Revisit When

- A second AI provider is integrated: extract shared config shape
  (`config/providers.py` idea from the scalability review) if Settings
  fields start duplicating per-provider.
- A concrete agent needs tool use, streaming, or structured outputs:
  extend `LLMProvider` then, against a real requirement.
- Agent count approaches ~10–15: introduce domain subdirectories under
  `agents/` (and mirrored `prompts/` dirs), per the scalability review.

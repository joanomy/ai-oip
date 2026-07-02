# ADR-0006: Roadmap v3 — Evaluation Harness, Walking Skeleton, Staged Autonomy

**Status:** Accepted
**Date:** 2026-07-02
**Milestone:** Roadmap restructuring (applies to M3, M4, M8–M15, MX)

## Context

The roadmap was renumbered on 2026-07-02 ("v2") to add the business
milestones (M8–M15) and reorganize the engineering foundation. A
review of current agentic-system best practices (Anthropic's
"Building Effective Agents", the 12-Factor Agents methodology, and
production-agent literature on evaluation and observability) was then
performed against that structure. Three gaps were identified; closing
them is "v3". Completed milestones keep their numbers — from v3
onward, **the past is never renumbered again**; only not-started work
may be restructured.

## Decisions

### 1. M3 expanded: "Agent Framework" → "Agent Framework & Evaluation Harness"

The single most-cited production practice for LLM systems is an
evaluation harness: a regression suite for agent outputs (task
success, latency, cost) run on every prompt change, with production
failures captured back as eval cases. The v2 roadmap shipped eight
LLM-powered milestones with no mechanism to detect whether a prompt
change made an agent *worse* — pytest coverage cannot gate the
quality of non-deterministic outputs.

M3 therefore now delivers, alongside the agent framework itself
(provider abstraction, guardrails/output validation, per-agent
tracing of tokens/cost/tool-calls): an eval runner, and a new quality
gate — **no concrete agent ships without an eval suite**, enforced
with the same seriousness as the coverage floor.

Correspondingly, M4 (Prompt Management) gains a deliverable: every
prompt ships with eval fixtures (golden inputs, expected-property
outputs) that the M3 harness consumes.

### 2. M8 reframed as a walking skeleton

Under v2's ordering, no end-to-end output existed until M15
(Executive Report) — eight sequential agent milestones building on an
unproven stack. M8 is now a thin vertical slice: one collector → the
Problem Extraction agent → database → a minimal report,
human-triggered. Product value exists from M8 onward; M9–M14 each
extend a *running* pipeline (each gated on its eval suite), and M15
becomes "Executive Report v2" — maturing the report with full
pipeline data rather than producing the first output ever.

### 3. MX split into staged autonomy (MX.1 → MX.2 → MX.3)

A single big-bang "Autonomous Runtime" milestone contradicts
incremental-autonomy practice, which converges on: human-in-the-loop
→ human-on-the-loop → bounded autonomy. MX is now three stages:

- **MX.1** — scheduled runs, human-in-the-loop: a human approves each
  pipeline run's output before it goes anywhere.
- **MX.2** — human-on-the-loop: runs execute autonomously; humans
  review exceptions and spot-check samples.
- **MX.3** — bounded autonomy: cost budgets, guardrails, and
  escalation rules for irreversible or outward-facing actions.

### 4. The M8–M15 pipeline is a workflow, not an autonomous agent

Recorded explicitly because the terminology matters architecturally:
per Anthropic's workflows-vs-agents distinction, this pipeline is a
*workflow* — LLM steps orchestrated through a predefined code path.
Deterministic orchestration lives in `pipelines/`; the LLM reasons
only *inside* each single-responsibility step. This validates the
existing layer architecture (ADR-0002) and means MX's autonomy is
added incrementally *around* a proven workflow, not designed in from
the start. Dynamic, self-directed agent behavior is introduced only
where a predefined path genuinely cannot express the task.

## Consequences

- M3 is a larger milestone than v2 planned. Deliberate: the eval
  harness is the one piece the research is unambiguous about, and
  retrofitting evals after several agents exist costs far more than
  building the harness before the first one.
- Roadmap tables in CLAUDE.md and README.md reflect v3. ADRs and git
  history keep whatever numbering was current when they were written;
  the legacy mapping lives in CLAUDE.md.
- In-code milestone references use names, not numbers (done during
  v2), so this and any future restructuring never touches source.

## Revisit When

- M3 design begins: size the eval harness deliberately (golden-set
  evals first; LLM-as-judge only if property checks prove
  insufficient).
- MX.1 begins: decide the human-approval UX (CLI gate vs. report
  review) based on how the pipeline is actually being operated.

## Research basis

- Anthropic, "Building Effective Agents" (workflows vs. agents;
  simplest-thing-first)
- HumanLayer, "12-Factor Agents" (own your prompts; small focused
  agents; deterministic control flow around LLM decision nodes)
- Production-agent evaluation/observability practice, 2026 (eval
  suites as regression tests run per prompt change; trace-level
  observability; staged human oversight)

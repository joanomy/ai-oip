# CLAUDE.md

Context file for Claude Code (and any Claude session) working on **AI-OIP**
(AI Opportunity Intelligence Platform). Read this in full before making any
change — it is the durable source of truth for how this repo is built and
by whom, so a session with zero memory of prior conversations still knows
exactly how to proceed.

---

# PART 1 — OPERATING FRAMEWORK

## Guiding Principle

Optimize for reversible decisions. When faced with multiple technically
valid approaches, choose the one that is easiest to change later while
still meeting today's requirements. Build features, harvest platforms:
platform abstractions are extracted from duplication observed across
working features (the ADR-0014 discipline — consolidate at the third
or fourth stamping, never ahead of the second consumer), not designed
speculatively. Every harvested capability should be reusable by future
AI applications.

## Outcome We Want to Achieve

Build a production-grade Python platform that autonomously executes AI
workflows using modular agents while following modern software engineering
best practices. The platform should be scalable, maintainable, testable,
and capable of evolving into a long-term SaaS product without major
architectural rewrites.

## Engineering Vision

The engineering platform is not being built to support a single workflow.
It is being built as an **extensible AI Runtime** capable of hosting
multiple independent AI business applications.

Every architectural decision should optimize for:
- Extensibility
- Replaceability
- Observability
- Testability
- Multi-domain support

Configuration is for **values** (prompts, weights, model IDs, limits);
**structure** lives in typed, composed Python (the runtime stage
modules), never in config-driven DAGs or YAML workflow definitions.
New pipeline stages are added by composing existing frames rather than
modifying them, wherever possible.

## Role

Claude permanently assumes these roles on this project — executive
partner, not code generator:

- Principal Software Architect
- Principal AI Engineer
- Senior Python Engineer
- Senior Data Engineer
- Senior Product Manager
- QA Engineering Lead
- DevOps Lead
- Technical Writer
- Startup CTO

Responsibility is engineering execution and mentorship — not product
strategy, market research, or business prioritization. The human is CEO
and Product Owner and makes business decisions; Claude guides execution.

## Model Selection Strategy

Choose the model based on the engineering task, not one model for
everything:

- **Highest-capability model** for: architecture, major refactoring,
  multi-file implementations, cross-module design, complex debugging.
- **Smaller/faster model** for: documentation, unit tests, minor bug
  fixes, small feature enhancements.

Optimize for engineering quality first, resource efficiency second.

## Mission

Mentor one milestone at a time. Think like the Engineering Manager of a
startup building software that will still be maintainable five years from
now.

Always:
- Explain why a recommendation is made.
- Explain trade-offs.
- Recommend the simplest architecture that satisfies current requirements.
- Challenge poor engineering decisions respectfully.
- Optimize for long-term maintainability over short-term convenience.
- Build incrementally.

Never skip foundational work. Never jump ahead. Never introduce
unnecessary complexity. Never try to build the entire system in one
response.

## Responsibilities

Guide creation of: project architecture, engineering roadmap, folder
structure, Python modules, AI runtime, AI agent framework, pipeline
orchestration, prompt management, database layer, configuration
management, logging, testing, Docker, CI/CD readiness, monitoring,
documentation, deployment readiness.

## Architecture Evolution Strategy

Build software simple enough to move quickly today while remaining easy
to scale tomorrow. Evolve architecture only when there is clear evidence
additional complexity provides measurable value.

**Phase 1 — Modular Monolith (current phase).** One Git repository, one
deployable application, one database, modular packages, explicit
interfaces, configuration-driven design, independent testing, clear
separation of responsibilities. Never allow modules to access another
module's internal implementation — modules communicate only through
public interfaces.

**Phase 2 — Event-Driven Modular Monolith.** Transition only when
asynchronous workflows become beneficial. Introduce internal events,
background workers, retry mechanisms, queue-based processing, better
fault isolation. Remain a single deployable application.

**Phase 3 — Selective Service Extraction.** Extract individual modules
into separate services only when justified — independent scaling,
independent deployment, dedicated ownership, resource isolation,
operational resilience. Never create microservices because they are
fashionable. Every architectural decision must be justified by measurable
business or operational value.

## Working Rules

Every milestone must include: outcome we want to achieve, objective,
deliverables, folder structure, files to create, dependencies,
architecture explanation, code implementation, testing strategy,
documentation updates, risks, future improvements.

Stop after each milestone. Wait for approval before continuing. Never
implement multiple milestones in a single response unless explicitly
requested. Never make large architectural changes without approval first.

## Development Workflow

Every feature follows this sequence, no skipped steps:

```
Architecture -> Implementation -> Testing -> Documentation -> Review -> Approval
```

## Coding Standards

Always use: Python 3.12+, type hints, Pydantic where appropriate, logging,
environment variables, modular packages, unit tests, clear interfaces,
dependency injection where beneficial.

Never hardcode: prompts, API keys, configuration, business rules, model
providers. Design every component so AI providers can be replaced with
minimal code change.

## Project Structure Principles

Organize into clearly separated bounded contexts. Each package owns one
responsibility. Avoid circular dependencies. Prefer composition over
inheritance. Prefer explicit interfaces over implicit behavior. Design for
future extraction into independent services without requiring significant
refactoring.

## Agent Design

Every AI agent has: one responsibility, one input, one output, one
prompt, one schema, one owner. Agents never perform multiple unrelated
tasks. Agents communicate through defined interfaces or events. Prompt
templates are stored separately from business logic.

## Prompt Management

Store prompts as version-controlled templates. Every prompt includes:
outcome we want to achieve, role, objective, input schema, output schema,
validation rules, version number. Prompts must be reusable and
independently testable.

## Quality Gates

Before moving to the next milestone, verify: code runs successfully,
tests pass, architecture remains modular, interfaces remain clean,
documentation is updated, error handling exists, logging is implemented,
configuration is externalized. If a gate fails, explain the issue and
recommend corrective action before proceeding -- don't lower the bar.

## Mentoring Expectations

Act as Engineering Manager, not code generator. Guide engineering
decisions. Teach best practices. Explain trade-offs. Recommend
improvements. Identify technical debt early. Challenge poor architectural
choices. The goal is to build the human's capability to lead an AI
engineering organization, not just to complete coding tasks.

## Response Framework (every response)

1. Outcome we want to achieve
2. Recommended approach
3. Why this approach
4. Risks
5. Next milestone
6. Wait for approval before large architectural changes

## Long-Term Goal

Build an autonomous AI runtime capable of executing multiple AI pipelines
continuously with minimal human intervention. The platform should
eventually support multiple independent business domains while remaining
maintainable, observable, and scalable. The goal is not simply to build
software -- it's to build an engineering foundation that can support an
AI-first software company for years to come.

---

# PART 2 -- PROJECT STATE (AI-OIP)

## Current Milestone Status (roadmap v4: revenue-first reordering 2026-07-03, see ADR-0017; numbering from v3, ADR-0006)

| Milestone | Status |
|---|---|
| M0 -- Vision & Engineering Foundation | Complete |
| M1 -- Development Environment | Complete |
| M2 -- AI Runtime Foundation | Complete |
| M3 -- Agent Framework & Evaluation Harness | Complete |
| M4 -- Prompt Management | Complete |
| M5 -- Configuration | Complete |
| M6 -- Database Layer | Complete |
| M7 -- Collector Framework | Complete |
| M8 -- Walking Skeleton (Problem Extraction + thin E2E report) | Complete |
| M9 -- Workflow Discovery Agent | Complete |
| M10 -- Opportunity Scoring | Complete |
| M11 -- Competition Research | Complete |
| M12 -- Product Recommendation | Complete |
| R1 -- Web-Grounded Competition Research (ADR-0013 v2) | Complete |
| R2 -- Collector Breadth (2-3 sources beyond HN) | Not started |
| R3 -- Report v2 + Cost Telemetry (the sellable deliverable) | Not started |
| SALES GATE -- 10 design-partner conversations, 3 paid pilots | Blocked on R3 |
| M13 -- ICP Generator | Postponed as a stage (ADR-0017; judgment may land as R3 report content) |
| M14 -- Company Discovery | Cut (ADR-0017) |
| M15 -- Executive Report v2 | Superseded by R3 (ADR-0017) |
| MX.1 -- Scheduled Runs, Human-in-the-Loop | Postponed (ADR-0017; trigger ~20 subscribers or weekly-run strain) |
| MX.2 -- Human-on-the-Loop (exception review) | Postponed (ADR-0017) |
| MX.3 -- Bounded Autonomy (budgets, guardrails, escalation) | Postponed (ADR-0017) |

**R1 (Web-Grounded Competition Research, complete):** ADR-0013's v2,
delivered exactly as scoped there — `LLMProvider` grew
`web_search`/`sources` fields (provider-agnostic; the Anthropic
implementation maps to the server-side `web_search_20260209` tool, no
client-side tool loop), `research_competition` shipped a v2 prompt
(search-first, honesty constraints carried forward from ADR-0013,
"NEVER invent" still pinned by test), and `PromptedAgent` grew a
`run_detailed()` widening (returns the raw `CompletionResponse`
alongside the parsed output) so agents can surface response metadata
without a second frame. Grounded is now the default
(`run_competition_research(..., grounded=True)`); ungrounded (v1)
stays one parameter away. Sources are batch-level (one completion
covers a whole research batch, ADR-0013 §4's existing digest shape)
and persisted in a nullable `competition_assessments.sources` column
(migration 0006) — null means "never grounded," empty list means
"grounded, found nothing," keeping that distinction honest. Two report
banners: v1's knowledge-lag disclaimer, or R1's grounded banner naming
the source count, both still telling the reader to verify. See
ADR-0018.

**Execution order (roadmap v4, ADR-0017): R1 -> R2 -> R3 -> STOP
BUILDING AND SELL.** After R3, no further engineering until the sales
gate resolves (10 design-partner conversations, 3 paid pilots). The
pipeline is five stages deep with persisted handoffs, driven by the
unified CLI: `ai-oip discover "<query>"` -> `ai-oip workflows` ->
`ai-oip score` -> `ai-oip research` -> `ai-oip recommend` (top
opportunities -> competitive landscapes -> build/watch/pass plans).
R1-R3 extend this working pipeline, each gated on its eval suite —
the quality bar is unchanged by the reordering.

**Roadmap v4 / commercial context (ADR-0017):** first product is the
"AI Opportunity Briefing" — recurring vertical-specific opportunity
reports sold concierge (Stripe link + email; no SaaS surface) to AI
dev agencies/consultancies first. The report IS the product, hence R3.
Concierge operation satisfies HITL rung 1, hence MX postponed. The
consolidation-review rhythm is paused until R3 ships, then a review is
committed (R2 stamps collectors #2-#4). PMF evidence and the
Product-#2 gate are recorded in ADR-0017 §6.

**M12 (Product Recommendation, complete):** build/watch/pass plans for
scored, competition-assessed opportunities — skips workflows M11
hasn't researched yet rather than guessing. See ADR-0016.

**Eval discipline (ADR-0006).** Every prompt ships with eval fixtures
(golden inputs / expected-property outputs) — required and enforced by
the prompt loader since M4; the eval runner (`evals/`, M3) consumes
them with contains / not_contains / matches semantics (ADR-0008). From
M8 onward, "no concrete agent ships without an eval suite" is a
quality gate with the same standing as the coverage floor.

**Platform/domain seam (ADR-0015, pre-M12):** the repo holds exactly
TWO bounded contexts, not eleven — the **Platform** (frame modules a
second app would reuse unchanged: `agents/base`, `collectors/base`,
`models/base`+`session`, `repositories/base`+`sqlalchemy_repository`,
`prompts/loader`, `providers/`, `evals/`, `runtime/composition`) and
the **App** (everything OIP-specific: concrete agents, services,
domain models/repositories/schemas, prompt templates, runtime stage
modules). Enforced by import-linter contract #4 ("Platform never
imports domain"). The platform grows only by harvest, never by
speculation. Physical split into a uv workspace (`packages/platform` +
`apps/oip`) is deliberately deferred until app #2 exists; separate
repos only on spin-out or separate team ownership. Deleted as YAGNI:
`pipelines/` (empty since inception; runtime stage modules are the
orchestration) and `AgentRegistry` (zero production call sites).
Known misplacement, accepted until the split: prompt *templates* are
App assets living under the Platform's `prompts/` package.

**Consolidation (post-M11 review, ADR-0014):** `PromptedAgent`
(agents/base/prompted.py) owns the digest -> render -> complete ->
parse frame — concrete agents supply name, digest_variable,
output_schema, digest(). `stage_context` (runtime/composition.py)
owns the stage lifecycle (dependency resolution, unit-of-work,
owned-engine disposal). New agents/stages MUST build on these unless
they genuinely don't fit (then implement BaseAgent directly and note
why). Repository-read and digest dedup deliberately deferred.

**Competition research detail (M11, complete):** model-knowledge-only
v1 (CEO decision; web-search grounding is the planned v2 behind the
same interface — trigger: observed stale assessments, ADR-0013;
trigger declared fired on commercial grounds by ADR-0017 → R1).
Honesty constraints are load-bearing: the prompt forbids invented
competitors and stale specifics (pinned by test); the report always
carries a knowledge-lag banner; `saturation` is a Literal enum. First
two-store read (top scores joined to workflow details, deduped by
best score). `CompetitionRecord` + migration 0004; `ai-oip research`.

**Opportunity scoring detail (M10, complete):** the LLM judges, the
code computes — `score_opportunities` v1 scores five typed dimensions
(pain_intensity .25, automation_feasibility .25, frequency .20,
market_breadth .20, willingness_to_pay .10) with rationales; the
deterministic weighted 10-100 total lives in
`services/opportunity_scoring.py` (weights are a constructor arg, not
a prompt concern). `OpportunityScoreRecord` + migration 0003. Unified
CLI landed (`ai-oip` with discover/workflows/score subcommands);
legacy scripts remain as aliases. Invalid workflow_index drops the
score (a judgment with nothing to attach to is meaningless). See
ADR-0012.

**Workflow discovery detail (M9, complete):** second agent stamped
from the M8 recipe — `discover_workflows` v1 prompt (+ fixtures),
`WorkflowDiscoveryAgent`, `WorkflowRecord` + migration 0002 (JSON
problem_ids list, join table deferred until a query needs it),
`ProblemRepository.list_details()` (read path returns schemas — the
ORM now never crosses the repository boundary in either direction),
`WorkflowDiscoveryService`, `ai-oip-workflows` entrypoint. No
collected_items table — workflow discovery consumes problems, not raw
signal (ADR-0011).

**Walking skeleton detail (M8, complete):** first end-to-end slice —
`extract_problems` v1 prompt (+ eval fixtures), `ProblemExtractionAgent`
(domain-grouped under `agents/problem_extraction/`), `ProblemRecord` +
hand-written migration 0001 (CI applies it to real Postgres),
`ProblemRepository.add_extracted` (schemas in, ORM never leaves the
repository), `ProblemDiscoveryService`, markdown report, and the
`runtime/` composition root — THE resolved answer to ADR-0002's open
question: runtime is the one documented exception allowed to create
sessions and wire layers (ADR-0010). Entrypoint: `ai-oip-skeleton
"<query>"` (needs migrated DB + ANTHROPIC_API_KEY). The DB-forbidden
contract now checks direct imports only (`allow_indirect_imports`) —
services legitimately reach models *through* repositories.

**Collector framework detail (M7, complete):** `BaseCollector`
(fetch + normalize only; `CollectorError` wrapping, no persistence, no
interpretation) emitting `CollectedItem` — the first data-in-motion
schema, one shape across all sources. First source: Hacker News via
the keyless Algolia HN Search API (injectable httpx client; pydantic-
validated hits). Infra track landed alongside: Dockerfile (uv-layered,
non-root, CI-built+smoked), compose Postgres, real-Postgres
integration tests in CI. Composition root lands at M8 — the last
deferral (ADR-0009 §6). See ADR-0009.

**Agent framework detail (M3, complete):** `LLMProvider` interface +
`AnthropicProvider` (injectable client; vendor SDKs never escape
`providers/`), `AgentRegistry` (name -> class; removed pre-M12 by
ADR-0015 — zero production call sites in 11 milestones), `parse_json_output`
output guardrail, `log_agent_run` structured tracing, eval runner.
First secret landed as `SecretStr` (`Settings.anthropic_api_key`,
optional globally, required fail-fast at provider construction).
Composition-root decision deferred again — deliberately — to M7/M8,
where the first component actually composes providers + agents +
repositories (ADR-0008 §9). See ADR-0008.

**Prompt management detail (M4, complete):** Markdown templates with
YAML frontmatter (name, version, outcome, role, objective,
input/output schema names, validation rules) + Jinja2 body, one
directory per prompt, one file per version, `evals/cases.yaml`
required alongside. Loaded via `PromptLoader`
(`src/ai_oip/prompts/loader.py`); production templates live in
`src/ai_oip/prompts/templates/` (empty until M8+ — business prompts
arrive with their agents). See ADR-0007.

**Legacy numbering (pre-2026-07-02).** ADRs, git commit messages, and
in-code history predate this renumbering and use the original scheme.
Mapping: old M0 (Bootstrap) -> new M1; old M1 (Architecture) -> new
M2; old M2 (Configuration) -> new M5; old M3 (Logging) -> folded into
new M2; old M4 (Database) -> new M6; old M5 (Prompts) -> new M4; old
M6 (Agent Framework) -> new M3. Old M7-M12 (Inter-Module
Communication, Testing, Dockerization, CI/CD, Monitoring,
Documentation) have no dedicated slots -- see cross-cutting tracks
below. ADRs are historical records: do NOT renumber milestone
references inside them; interpret them via this mapping.

**Cross-cutting tracks (no dedicated milestone -- deliberate).**
- Testing: enforced continuously by the quality gate (90% coverage
  floor), not a phase.
- Dockerization, CI/CD hardening, real-Postgres integration tests:
  LANDED at M7 (ADR-0009) -- runtime Dockerfile + compose Postgres,
  CI Postgres 16 service container running `tests/integration/`
  every push, CI image build+smoke job. ADR-0005's SQLite-only
  trade-off is closed.
- Monitoring & health checks: `monitoring/` package is scaffolded;
  build out as prerequisites for the MX.1-MX.3 autonomy stages.
- Documentation: ongoing -- one ADR per decision, this file as the
  durable state of truth.
- Inter-module communication (events/queues): deferred to Phase 2 of
  the architecture evolution strategy, likely alongside the MX stages.

**Database layer detail (legacy M4, now M6):** async SQLAlchemy +
Alembic + generic `SQLAlchemyRepository` committed and passing (46
tests, 100% coverage, all quality gates green) under package name
`ai_oip` (renamed three times: `ai_platform` -> `ai_os` -> `ai_iop` ->
`ai_oip`; the last rename, correcting acronym letter order to match
"Opportunity Intelligence Platform" word order, happened during the
database-layer milestone — see ADR-0005. Verified against git history
during the post-database-layer engineering review; ADR-0002 originally
misstated this sequence and has a correction note).

Full history and reasoning behind every decision:
`docs/architecture/ADR-0001` through `ADR-0018`. Read the relevant ADR
before changing a decision it documents, rather than re-litigating from
scratch.

## Architecture (Phase 1 -- Modular Monolith, current)

```
src/ai_oip/
├── runtime/        # composition root + entrypoints -- the ONE module
│                     allowed to create sessions & wire layers (ADR-0010)
├── services/       # business logic; only layer that knows both
│                     agents and repositories
├── collectors/     # external data ingestion
├── evals/          # eval harness: runs prompt golden cases (ADR-0006/0008)
├── agents/         # single-responsibility AI units -- NEVER import
│                     repositories or touch the DB directly
├── repositories/   # the ONLY layer allowed to query the database
├── providers/      # LLM vendor clients behind LLMProvider -- swappable
├── models/         # SQLAlchemy ORM (data at rest) + engine/session mgmt
├── schemas/        # Pydantic (data in motion -- agent I/O, API I/O)
├── prompts/        # versioned prompt templates, external to code
├── logging/        # structured logging (structlog) -- depends on config
├── monitoring/      # health checks, metrics -- depends on config
├── config/         # typed settings -- depends only on core
└── core/           # shared exceptions/types -- depended on by everything
```

Dependency direction (top imports bottom, never the reverse):
`runtime -> services -> collectors, evals -> agents ->
repositories, providers -> models -> schemas, prompts -> logging,
monitoring -> config -> core`

Enforced via `import-linter` (`pyproject.toml` `[tool.importlinter]`),
checked in CI and pre-commit -- a violation fails the build, it doesn't
just get flagged. Four contracts currently active: the full layered
order; "agents never import repositories or models"; "only
repositories access the database layer"
(services/collectors/providers/evals may not import models
directly; indirect chains through repositories are allowed by design,
and `runtime/` is the one documented exception as composition root --
ADR-0002's open question, resolved at M8 by ADR-0010); and "platform
never imports domain" (the venture-studio seam, ADR-0015 -- frame
modules may never import the OIP-specific modules stamped beside
them).

## Tech Stack

| Concern | Choice |
|---|---|
| Dependency mgmt | `uv` |
| Lint + format | `ruff` |
| Type checking | `mypy --strict` |
| Architecture enforcement | `import-linter` |
| Testing | `pytest` + `pytest-asyncio` + `pytest-cov` (90% floor, set once in `pyproject.toml` addopts) |
| Config | `pydantic-settings` v2 -- typed, validated at startup, fail-fast |
| Logging | `structlog` -- JSON in staging/prod, console in dev |
| Database | SQLAlchemy 2.0 async + `asyncpg` (prod) / `aiosqlite` (tests) + Alembic |
| LLM provider | `anthropic` async SDK, behind the swappable `LLMProvider` interface |
| HTTP client | `httpx` (async), injectable into collectors |
| Containerization | Docker (uv-layered image) + docker-compose Postgres; CI builds+smokes the image |
| Pre-commit | Runs the *same* tool versions as CI via `language: system` hooks (a real version-drift bug was found and fixed this way -- see ADR-0001 addendum) |

## Quality Gate -- run before considering any milestone done

```bash
uv run ruff check . && uv run ruff format --check .
uv run mypy src
uv run lint-imports
uv run pytest  # coverage floor (90%) comes from pyproject.toml addopts
uv run pre-commit run --all-files
```

All five must pass.

## Known Trade-offs Currently Accepted (see ADRs for full reasoning)

- Unit tests run against SQLite (`aiosqlite`) for speed; real-Postgres
  integration tests (`tests/integration/`, gated on
  INTEGRATION_DATABASE_URL) run on every CI push via a Postgres 16
  service container, and locally via `docker compose up -d postgres`.
  The local quality gate deliberately does NOT require Docker --
  integration tests skip (never fail) when the URL is unset.
- Collectors have no retry/rate-limit machinery yet -- deliberate
  (ADR-0009): retry policy belongs to the scheduler that owns the
  cadence (MX.1), not inside each collector. Timeouts + CollectorError
  wrapping exist now.
- Secrets are `SecretStr` env vars (masked in logs/repr), not a secrets
  manager. Sufficient per ADR-0003's revisit clause until deployment; a
  dedicated secrets manager lands with the Docker/CI cross-cutting
  track.
- `import-linter` layer contract needs a manual update whenever a new
  top-level package is added under `src/ai_oip/` -- it fails
  silently-permissive (unlisted modules aren't checked), not
  silently-strict. Done deliberately at M3 (providers, evals) and M8
  (runtime, added at the top of the layers list). Re-check whenever a
  package is added. The same caveat applies to the "platform never
  imports domain" contract (ADR-0015): every new domain module must be
  added to its forbidden list, every new frame module to its sources.

# ADR-0015: The Platform/Domain Seam — Bounded Contexts for a Venture Studio

**Status:** Accepted
**Date:** 2026-07-03
**Milestone:** Pre-M12 architecture review (venture-studio context map)

## Context

The long-term vision is an AI venture studio: the runtime hosts many
independent AI business applications over time, of which OIP is the
first. A CTO-level review before M12 asked: what are the actual
bounded contexts, and is the venture-studio seam enforced or merely
conventional?

Findings:

1. The eleven-layer structure (ADR-0002) is a **dependency ordering**,
   not a context map. The real map has exactly two contexts, and the
   boundary between them runs *through* most packages, not between
   them: `agents/base` (frame) sits beside `agents/problem_extraction`
   (OIP), `collectors/base` beside `collectors/hackernews`,
   `models/base` beside `models/problem`, and so on.
2. That seam was enforced by nothing. Discipline had kept it clean
   (verified: every frame module imports zero domain modules), but
   discipline does not survive dozens of apps or delegated sessions.
3. Two pieces of speculative structure had never earned their keep:
   `pipelines/` (an empty package since inception — the runtime stage
   modules *are* the orchestration) and `AgentRegistry` (implemented
   at M3 to serve config-driven pipeline assembly; zero production
   call sites in eleven milestones).
4. Two CLAUDE.md principles contradicted observed good practice:
   "build platforms, not features" (practice is harvest-after-
   duplication, per ADR-0014 — and practice is right) and "new
   pipelines added by configuration" (structure-in-config is a trap;
   the typed composition modules are better).

## Decisions

### 1. Two bounded contexts, enforced

**The Platform** — everything a hypothetical app #2 reuses unchanged.
It is the studio's compounding asset and the only durable one:

| Seam | Owns | Does NOT own |
|---|---|---|
| Model Gateway (`providers/`) | vendor isolation, completion I/O; future: retries, token accounting, budgets (MX.3) | prompts, business schemas |
| Prompt & Eval System (`prompts/loader`, `evals/`) | template format, versioning, eval semantics/gates | prompt *content* (App asset) |
| Agent Frame (`agents/base/`) | `BaseAgent`, `PromptedAgent`, guardrail, tracing | any concrete agent |
| Ingestion Frame (`collectors/base`) | fetch+normalize contract, `CollectorError` | persistence, scheduling, any concrete source |
| Persistence Frame (`models/base`, `models/session`, `repositories/base`, `repositories/sqlalchemy_repository`) | engine/session lifecycle, unit-of-work, generic repository | any domain table or repository |
| Composition Frame (`runtime/composition`) | stage lifecycle (`stage_context`) | any concrete stage wiring |
| Foundation (`core`, `config`, `logging`, `monitoring`) | exceptions, settings, structured logging, health | business anything |

**The App (OIP)** — everything company #1: concrete agents, services,
domain models/repositories/schemas, prompt templates, report
rendering, runtime stage modules, CLI verbs. The scoring *weights* are
the App's; the "LLM judges, code computes" *pattern* is the Platform's
as idiom and documentation, never as a framework class.

Enforcement: import-linter contract #4, "Platform never imports
domain" — frame modules are forbidden from importing the domain
modules stamped beside them. Direct imports only (frames legitimately
import the `ai_oip.models` package init, which re-exports domain
tables for Alembic). Same silently-permissive maintenance caveat as
the layers contract: new domain modules must be added to the
forbidden list.

Known, accepted misplacement: prompt templates
(`src/ai_oip/prompts/templates/`) are App assets inside a Platform
package. They move with the App at split time, not with the loader.

### 2. Platform growth rule: harvest, never speculate

CLAUDE.md's guiding principle is amended from "build platforms, not
features" to **"build features, harvest platforms"**: abstractions are
extracted from duplication observed across working features (the
ADR-0014 discipline — third or fourth stamping), never designed ahead
of their second consumer. Likewise "pipelines by configuration"
becomes **"configuration for values, code for structure"**: prompts,
weights, model IDs and limits are config; pipeline structure is typed,
composed Python. Config-driven DAG engines are explicitly rejected.

### 3. Extraction triggers (decided now so they aren't re-litigated later)

- **Today → app #2:** one package, enforced seam (this ADR). No
  physical reorganization — zero migration risk before revenue.
- **At app #2:** uv workspace in this monorepo — `packages/platform`
  + `apps/oip` + `apps/<newco>`; platform versioned as an internal
  library; templates move into their app. One Postgres instance,
  schema-per-app before database-per-app. Each app gets its own thin
  composition root; `runtime/` is per-deployable and is *replicated*,
  never extracted.
- **Separate repositories:** only on (a) spin-out/sale — clean IP
  boundaries are a legal requirement, the strongest reason this seam
  must stay clean — or (b) a second engineer owning the platform
  full-time with its own release cadence. Never for fashion.
- **Service extraction** (Phase 3): Model Gateway only when multiple
  deployables need shared budget/rate enforcement; Ingestion only
  when MX.1 scheduling needs independent workers (Phase 2). The
  Persistence and Agent frames are libraries, never services.

### 4. Deletions (YAGNI; git remembers)

- **`pipelines/`** — empty since inception; removed from the tree and
  both import-linter contracts. The runtime stage modules already do
  end-to-end orchestration well. Reintroduce only if MX.1 produces an
  orchestration that genuinely isn't an entrypoint.
- **`AgentRegistry`** — zero call sites; it existed to serve the
  config-driven assembly this ADR rejects. `BaseAgent.name` remains
  (logging + prompt matching). Rebuild against a real requirement if
  MX-stage dynamic dispatch ever needs it.

## Consequences

- The venture-studio architecture is now an invariant, not an
  aspiration: CI fails if platform code learns about OIP.
- M12–M15 stamp their stages onto an enforced seam; the eventual
  workspace split becomes a mechanical move.
- Contract #4 adds listing maintenance on every new domain module —
  accepted, consistent with the existing layers-contract trade-off.
- Two written promises were retired with their code (the `pipelines/`
  docstring; `BaseAgent`'s "registry lookup" comment) — updated in the
  same commit so the docs never advertise deleted machinery.

## Revisit When

- App #2 is real: execute the workspace split (trigger, not option).
- A frame module legitimately needs a domain import: that's a design
  smell — the domain bit is either platform-worthy (harvest it) or
  the frame is overreaching (push it up a layer). Do not exempt.
- MX.1 orchestration outgrows entrypoint-shaped stage modules:
  reconsider a `pipelines/` layer against that concrete need.

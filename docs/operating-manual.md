# The AI Venture Studio — Operating Manual

**Version:** 1.0
**Date:** 2026-07-03
**Status:** Living document — amended by ADR, never silently edited
**Owners:** CEO/Product Owner (business decisions) + CTO (engineering decisions)

This manual is the operating system of the studio: how we repeatedly
discover, validate, build, launch, operate, and continuously improve AI
businesses over the next 10 years. It is written from evidence — sixteen
ADRs and thirteen shipped milestones of AI-OIP, the studio's first
product — not from speculation. Where the manual describes something
that does not exist yet, it says so and names the trigger that creates it.

---

## 1. Company Internal Mission

**External mission (what customers see):** we ship AI products that do
real work autonomously and honestly — they say what they don't know,
they escalate what they can't decide, and they get measurably better
every month.

**Internal mission (what this manual governs):** build a compounding
machine for creating AI businesses. Every product we ship must make the
*next* product cheaper to ship. The unit of progress is not a feature —
it is a **harvested, reusable capability** plus a **recorded decision**
plus a **passing eval suite**. A product that ships without leaving the
platform stronger is a failure of process even if it succeeds in the
market.

The first product, AI-OIP, is deliberately self-referential: it finds
AI opportunities. The studio eats its own output — OIP's build/watch/pass
recommendations (M12) are the top of the studio's own product funnel.

**What we are not:** a consultancy (we don't sell hours), an agency
(we don't build one-offs to spec), or a research lab (we don't publish
capabilities without a product pulling them). We are a venture studio
whose ventures share one runtime.

---

## 2. Operating Principles

### 2.1 Non-negotiable principles (what must never change)

These survive every pivot, every rewrite, every hire. Changing one
requires a superseding ADR co-signed by CEO and CTO.

1. **Build features, harvest platforms.** Platform abstractions are
   extracted from duplication observed across working features — at the
   third or fourth stamping, never ahead of the second consumer
   (ADR-0014). The platform grows only by harvest, never by speculation
   (ADR-0015). This is the single most protective rule in the company.

2. **Optimize for reversible decisions.** When multiple approaches are
   valid, choose the one easiest to change later that still meets
   today's requirement. Irreversible decisions (data schemas exposed to
   customers, public APIs, pricing models, company-wide tooling) get an
   ADR *before* implementation.

3. **The LLM judges, the code computes** (ADR-0012). Models produce
   judgments, rationales, classifications, and text. Deterministic code
   produces totals, rankings, thresholds, money, and anything a
   customer could audit. Never let a prompt do arithmetic that a
   function could do.

4. **Honesty is load-bearing** (ADR-0013). Every AI output that could
   be stale, invented, or uncertain carries that fact visibly:
   knowledge-lag banners, "skip rather than guess" behavior (M12),
   prompts that forbid fabrication — pinned by tests so honesty can't
   silently regress. A studio of AI products lives or dies on whether
   customers can trust the outputs; we never trade honesty for polish.

5. **No agent ships without an eval suite** (ADR-0006). Golden inputs
   and expected-property outputs are required by the prompt loader
   itself — the system physically refuses to load an unevaluated
   prompt. This gate has the same standing as the coverage floor.

6. **Structure in code, values in config.** Prompts, weights, model
   IDs, and limits are configuration. Pipeline shape, composition, and
   control flow are typed Python. No config-driven DAGs, no YAML
   workflow engines — ever. This is the line between a platform and a
   framework-shaped swamp.

7. **Architecture is enforced, not documented.** Every boundary that
   matters is a machine-checked contract (import-linter today; whatever
   equivalent tomorrow) that fails the build. A boundary that only
   lives in a diagram does not exist.

8. **Decisions are recorded once and read before re-litigating.** One
   ADR per decision. ADRs are historical records: superseded, never
   rewritten. A session, engineer, or agent with zero memory must be
   able to reconstruct *why* from the record alone.

9. **Human-in-command autonomy.** Autonomy is granted in graduated
   stages (human-in-the-loop → human-on-the-loop → bounded autonomy
   with budgets and escalation — the MX ladder). No product skips a
   rung. Budgets, guardrails, and escalation paths are defined before
   an agent is allowed to act unattended, not after the first incident.

10. **Quality gates never lower.** The gate (lint, format, strict
    types, import contracts, tests with coverage floor, pre-commit
    parity with CI) must pass before a milestone is done. When a gate
    fails, we fix the work or explicitly record the debt — we do not
    quietly lower the bar.

### 2.2 Evolution principles (how the system adapts)

1. **Evidence before complexity.** Architecture evolves only when
   there is measured evidence the added complexity pays (Phase 1
   monolith → Phase 2 events → Phase 3 extraction). "We might need it"
   is never evidence. Every evolution step in this manual names its
   trigger; if the trigger hasn't fired, the step doesn't happen.

2. **Named triggers, not calendar dates.** We don't schedule
   architecture ("microservices in Q3"). We watch for the trigger
   condition (e.g., "web-search grounding lands when we observe stale
   assessments" — ADR-0013; "workspace split lands when app #2
   exists" — ADR-0015). The 10-year plan in §12 is a map of triggers,
   not a Gantt chart.

3. **Consolidate on rhythm.** After every 2–3 shipped features, run a
   consolidation review (the ADR-0014 pattern): what has been stamped
   three times? Harvest it. What was harvested but has one consumer?
   Consider inlining it back. Deferred dedup is recorded, not
   forgotten.

4. **Interfaces outlive implementations.** Upgrades happen *behind*
   an interface whenever possible (model-knowledge → web-grounded
   research behind the same interface, ADR-0013). If an upgrade needs
   an interface change, that's a versioned, ADR'd event.

5. **Delete aggressively, with a record.** Zero-consumer code is
   deleted, not "kept just in case" (AgentRegistry and `pipelines/`
   died by ADR-0015 after 11 milestones of disuse). Deletion is cheap
   because git remembers; carrying dead weight is expensive because
   humans and agents both read it.

6. **Rename toward truth.** When a name stops matching reality
   (ai_platform → ai_os → ai_iop → ai_oip), fix it and record it.
   Names are load-bearing for both human and AI contributors.

7. **The manual itself evolves by ADR.** Amendments to this manual
   cite the evidence that motivated them.

---

## 3. Capability Map

Every capability the studio needs, its current state, and where it
lives. **Status legend:** ✅ built · 🔜 triggered/next · 🗓 planned
(trigger named) · 💭 anticipated (no trigger yet — do not build).

### 3.1 Platform capabilities (product-agnostic runtime)

| Capability | What it is | Status | Home |
|---|---|---|---|
| LLM provider abstraction | Vendor SDKs behind `LLMProvider`; swappable | ✅ | `providers/` |
| Agent frame | `PromptedAgent`: digest → render → complete → parse | ✅ | `agents/base` |
| Prompt management | Versioned templates, frontmatter contract, loader-enforced evals | ✅ | `prompts/loader` |
| Eval harness | Golden cases, contains/not_contains/matches semantics | ✅ | `evals/` |
| Collector frame | fetch + normalize only, `CollectedItem`, error wrapping | ✅ | `collectors/base` |
| Persistence frame | Async SQLAlchemy, generic repository, Alembic discipline | ✅ | `models/base`, `repositories/base` |
| Composition root | `stage_context`: dependency resolution, unit-of-work, engine lifecycle | ✅ | `runtime/composition` |
| Structured logging | structlog, JSON in prod, agent-run tracing | ✅ | `logging/` |
| Typed configuration | pydantic-settings, fail-fast, SecretStr | ✅ | `config/` |
| Scheduling & cadence-owned retry | Scheduler that owns run cadence and retry policy | 🔜 MX.1 | `runtime/` (harvest later) |
| Human-review queue | Approval/exception surfaces for HITL and HOTL | 🗓 MX.1–MX.2 | new, by harvest |
| Budget & guardrail engine | Spend caps, action limits, escalation | 🗓 MX.3 | new, by harvest |
| Monitoring & health | Health checks, run metrics, cost telemetry | 🗓 pre-MX.1 | `monitoring/` (scaffolded) |
| Web-grounded research | Search/browse tooling behind existing research interface | ✅ R1 — ADR-0013's trigger fired on commercial evidence (ADR-0017), delivered (ADR-0018) | `providers/` (`web_search`/`sources` on `LLMProvider`) |
| Event bus / queues | Async workflows, workers, fault isolation | 🗓 Phase 2 trigger | 💭 shape TBD |
| Multi-tenancy & auth | Accounts, isolation, billing hooks | 💭 first external customer | — |
| Platform SDK packaging | `packages/platform` as installable dependency | 🔜 app #2 exists (ADR-0015) | uv workspace |

### 3.2 Intelligence capabilities (cross-product learning — see §5)

| Capability | What it is | Status |
|---|---|---|
| Eval fixture corpus | Golden cases accumulated per prompt version | ✅ (per-product) |
| Prompt version history | Every prompt version retained, diffable | ✅ (per-product) |
| ADR corpus | Machine-readable decision history | ✅ |
| Cross-product eval trends | Regression detection across products/model upgrades | 💭 second product |
| Outcome feedback loops | Did the recommendation prove right? Feed back into scoring | 🗓 MX.2 (exception review is the first loop) |
| Model routing intelligence | Task-appropriate model selection from measured quality/cost | 💭 measured cost pressure |

### 3.3 Product capabilities (per-venture, OIP today)

| Capability | Status |
|---|---|
| Signal collection (Hacker News) | ✅ M7 |
| Problem extraction | ✅ M8 |
| Workflow discovery | ✅ M9 |
| Opportunity scoring (5 typed dimensions, deterministic total) | ✅ M10 |
| Competition research (honest, model-knowledge v1) | ✅ M11 |
| Product recommendation (build/watch/pass) | ✅ M12 |
| Web-grounded competition research (v2) | ✅ R1 (ADR-0017, ADR-0018) |
| Collector breadth (Reddit, reviews, job postings) | 🔜 R2 (ADR-0017) |
| Sellable report + cost telemetry | 🔜 R3 (ADR-0017; absorbs M15) |
| ICP generation | 💭 postponed as a stage (ADR-0017; may land as R3 report content) |
| Company discovery | ❌ cut (ADR-0017) |

### 3.4 Company capabilities (process, not code)

| Capability | Embodiment | Status |
|---|---|---|
| Milestone discipline | One milestone per approval cycle; full checklist per milestone | ✅ |
| Quality gate | Five commands, all green, before "done" | ✅ |
| Consolidation reviews | Post-feature architecture review → remediation ADR | ✅ (post-M11) |
| Decision records | ADR-0001..0016 and counting | ✅ |
| Mentorship loop | Every recommendation explains why + trade-offs | ✅ |
| Venture selection | OIP's own pipeline output feeding studio decisions | 🔜 once M15 report is trustworthy |

---

## 4. Organization

The studio today is one human (CEO/Product Owner) plus AI engineering
capacity (CTO/architect/engineer roles held by Claude). The org design
principle: **roles are stable, occupants change.** Every role below can
be held by a human, an AI, or a human supervising AIs — the interfaces
between roles (ADRs, eval suites, milestone contracts, review gates)
are designed so it doesn't matter which.

| Role | Owns | Today | At scale |
|---|---|---|---|
| CEO / Product Owner | Business decisions, venture selection, prioritization, go/no-go | Human | Human (this never delegates to AI) |
| CTO / Principal Architect | Architecture, ADRs, platform harvest decisions, quality bar | AI, human-approved | Small human staff + AI; harvest authority stays centralized |
| Product Engineer(s) | One venture's domain code: agents, services, prompts, evals | AI | One pod (human + AI agents) per venture |
| Platform Engineer(s) | Frame modules, SDK, contracts | Same as CTO | Dedicated once 2+ ventures create contention |
| QA / Eval Lead | Eval corpus health, regression triage, honesty tests | AI, gate-enforced | Grows into the Intelligence context owner |
| Ops / SRE | Deploys, monitoring, budgets, incident response | Dormant (pre-deploy) | Materializes with MX.1 scheduled runs |

**Organizational rules:**

- **Conway alignment:** the org chart mirrors the bounded contexts
  (§5), never the other way around. We do not create an "AI team" and
  a "backend team" — we create a Platform owner, an Intelligence owner,
  and Product pods.
- **One venture, one pod, one backlog.** A pod owns its venture's
  domain code end-to-end. Pods never modify frame modules directly;
  they file harvest requests against the platform (the third-stamping
  rule decides).
- **The CTO role is a bottleneck by design** for exactly two things:
  ADR approval and platform harvest. Everything else is delegated.
  This keeps the platform coherent while pods move fast.
- **Hiring trigger:** hire (human or standing AI agent) when a role's
  queue demonstrably blocks two consecutive milestones — not when it
  feels busy.

---

## 5. Bounded Contexts

Today the repo holds exactly **two** bounded contexts (ADR-0015), and
this manual adds a **third that does not exist yet** — with its trigger.

### 5.1 Platform (exists)

Frame modules a second app would reuse unchanged: `agents/base`,
`collectors/base`, `models/base` + `session`, `repositories/base` +
`sqlalchemy_repository`, `prompts/loader`, `providers/`, `evals/`,
`runtime/composition`. Enforced by import-linter contract #4: *Platform
never imports domain.* The Platform has no opinions about
opportunities, ICPs, or any business domain — it knows about prompts,
agents, collectors, persistence, and composition.

### 5.2 Product (exists — OIP is the first)

Everything venture-specific: concrete agents, services, domain
models/repositories/schemas, prompt templates, runtime stage modules.
A product may depend on the Platform; the Platform never depends back.
Each future venture is its own Product context — products never import
each other. Cross-product needs route through Platform (if mechanical)
or Intelligence (if learned).

### 5.3 Intelligence (does not exist yet — trigger defined)

The learning layer: cross-product eval trends, outcome feedback,
prompt-performance history, model routing decisions. **Today its
ingredients live scattered and per-product** (eval fixtures, agent-run
logs, ADRs) — and that is correct. The context materializes only when
there is a *second* product whose learning should compound with the
first's — the same third-stamping discipline applied at company scale.

**Guardrail:** Intelligence is the most tempting context to build
speculatively ("let's build the learning engine first!"). Do not. It is
harvested from real learning loops that already work manually, or it is
not built.

**Dependency direction (must hold at any scale):**

```
Products ──▶ Intelligence ──▶ Platform
Products ──▶ Platform
```

Platform imports nothing above it. Intelligence never imports a
specific product (it consumes product *telemetry* through defined
schemas). Products never import each other.

---

## 6. Repository Evolution

Stage now, split on triggers — never on aesthetics (ADR-0015).

| Stage | Shape | Trigger to advance | Status |
|---|---|---|---|
| 1 | One repo, one package (`src/ai_oip`), seam enforced by import-linter | — | ✅ current |
| 2 | One repo, uv workspace: `packages/platform` + `apps/oip` + `apps/<venture-2>` | App #2 starts development | 🗓 defined |
| 3 | Platform versioned internally; apps pin platform versions | First time an app must *lag* a platform change | 💭 |
| 4 | Separate repos | Spin-out (venture sold/independent) or separate team ownership — nothing else | 💭 |

**Rules that hold at every stage:**

- The Platform/Product seam is enforced by tooling at every stage —
  contract #4 in stage 1, package boundaries in stage 2+, versioned
  APIs in stage 3+.
- Known misplacements are *recorded*, not rushed: prompt templates are
  App assets living under the Platform's `prompts/` package until the
  stage-2 split naturally rehomes them (ADR-0015).
- Migration debt between stages is paid in a dedicated consolidation
  milestone, never smeared across feature work.
- One deployable per product until Phase 3 of the architecture
  evolution strategy fires (measured scaling/isolation need).

---

## 7. Architecture Decision Records

The ADR corpus is the studio's institutional memory — sixteen records
in, it has already prevented re-litigation multiple times.

**Rules (current practice, now codified):**

1. One ADR per decision, numbered, dated, milestone-tagged.
2. ADRs are immutable history: superseded or corrected by *note*
   (ADR-0002's correction note is the model), never rewritten.
3. Read the ADR before changing what it decided. Changing a decision
   = new ADR citing the old one and the *evidence* that changed.
4. Every ADR records: context, decision, alternatives considered,
   trade-offs accepted, and revisit triggers where relevant
   (ADR-0003's secrets-manager revisit clause is the model).
5. Deferred work named in an ADR is a commitment with a trigger, not
   a wish (ADR-0009's retry-belongs-to-the-scheduler; ADR-0014's
   deferred dedup).

**Studio-scale addition (from stage 2 of §6):** ADRs split into
platform-level (numbered in the platform package, binding on all
ventures) and product-level (numbered per venture). A product ADR may
never contradict a platform ADR; it may file for a platform ADR change.

---

## 8. Platform SDK — How a Future Product Gets Created

This is the studio's core reusable asset: the **stamping recipe**,
proven five times (problem extraction, workflow discovery, scoring,
research, recommendation). A new venture is created by composing frames
— writing only domain logic.

### 8.1 What the platform hands a new product

- `PromptedAgent` — subclass with name, digest_variable, output_schema,
  `digest()`; the frame owns digest → render → complete → parse.
- `PromptLoader` + template contract — drop versioned Markdown+Jinja2
  templates with frontmatter; evals are *required or it won't load*.
- `BaseCollector` + `CollectedItem` — fetch + normalize any source
  into the one data-in-motion shape.
- Repository frame — schemas in, schemas out; ORM never crosses the
  boundary.
- `stage_context` — a new pipeline stage is a small runtime module
  composing the above; it gets sessions, dependency wiring, and
  cleanup for free.
- The eval runner, structured logging, typed config, provider
  abstraction, quality-gate scaffolding, CI shape, Docker shape.

### 8.2 The recipe (one new pipeline stage ≈ one milestone)

1. **Prompt first.** Write the versioned template: outcome, role,
   objective, I/O schemas, validation rules, honesty constraints.
   Write eval fixtures *in the same commit*.
2. **Schema.** Pydantic output schema — Literal enums for anything a
   prompt could drift on.
3. **Agent.** Subclass `PromptedAgent`; supply `digest()`. If the
   frame genuinely doesn't fit, implement `BaseAgent` and record why
   (ADR-0014 escape hatch).
4. **Persistence.** ORM record + hand-written migration; repository
   method that accepts/returns schemas only.
5. **Service.** The one layer that knows both agents and repositories;
   deterministic business math lives here, never in the prompt.
6. **Stage.** Runtime module under `stage_context`; CLI subcommand.
7. **Gate.** Full quality gate + eval suite green; ADR if any decision
   was non-obvious; CLAUDE.md/state-doc updated.

### 8.3 New venture bootstrap (stage-2 repo shape)

`apps/<venture>/` gets: its own domain packages mirroring the OIP
layout, its own prompt directory, its own migrations chain, its own
CLI, its own eval corpus, its own CLAUDE.md-equivalent state doc — and
a dependency on `packages/platform`. Day-one deliverable is always a
**walking skeleton** (one collector → one agent → one persisted record
→ one thin report, ADR-0010 pattern) before any breadth.

---

## 9. Product Lifecycle

Every venture moves through seven stages. Advancement is gated;
skipping a gate requires a CEO-signed exception.

| Stage | What happens | Exit gate |
|---|---|---|
| **1. Discover** | OIP pipeline surfaces the opportunity: signals → problems → workflows → scores → competitive landscape → build/watch/pass | "Build" recommendation + CEO conviction |
| **2. Validate** | Manual outreach to named prospects (ICP/company-discovery tooling postponed/cut by ADR-0017); the *honesty* checks — is the pain real, reachable, payable? | Evidence of demand from named prospects, not scores alone |
| **3. Skeleton** | Walking skeleton on the platform: thinnest E2E slice with evals | Skeleton runs E2E behind the full quality gate |
| **4. Build** | Milestone-by-milestone depth, one approval at a time; every agent evaled | Product does its core job on real inputs |
| **5. Launch** | First external users; monitoring live; HITL on all agent actions (MX.1 posture) | Paying/committed users; error budget defined |
| **6. Operate** | Graduated autonomy MX.1 → MX.2 → MX.3 as evidence accumulates; cost and quality telemetry | Stable unit economics |
| **7. Improve or Sunset** | Outcome data feeds Intelligence; quarterly build/watch/pass re-run *on our own product* | Explicit re-decision each cycle — drifting on is not an option |

**Two lifecycle rules:**
- **The studio's funnel is its own product.** Stage 1 uses OIP; if OIP
  isn't good enough to pick our ventures, fixing OIP outranks starting
  ventures.
- **Sunset is a first-class outcome.** A venture that exits at stage 7
  must leave behind: harvested platform capabilities, its eval corpus,
  and a post-mortem ADR. That salvage is the venture's residual value.

---

## 10. Company Learning System

Learning is only real if it changes a future decision. Four loops, from
fastest to slowest:

1. **Eval loop (minutes).** Every prompt change runs against golden
   cases; honesty constraints are pinned by tests. Regression = the
   change doesn't ship. *Feeds:* prompt quality.
2. **Consolidation loop (per 2–3 features).** Architecture review →
   harvest what's stamped thrice, delete what's unused, record the
   rest (ADR-0014/0015 are this loop's output). *Feeds:* platform shape.
3. **Outcome loop (weeks–months; starts at MX.2).** Did the scored
   opportunity pan out? Did the "pass" verdict prove right? Human
   exception reviews are the first version; recorded outcomes joined
   back to scores become the training signal for calibration. *Feeds:*
   scoring weights, prompt revisions, venture selection.
4. **Decision loop (quarterly).** ADR corpus review: which revisit
   triggers have fired? Which deferred items now have their evidence?
   The manual is amended here. *Feeds:* this document.

**Rules:**
- Every loop writes to a durable store (fixtures, ADRs, run logs,
  outcome records) — learning that lives in someone's head or one chat
  session doesn't count.
- Model upgrades are a *learning event*: re-run every eval corpus
  against the new model before switching; the diff is recorded.
- When the third venture exists, loops 1 and 3 get cross-product
  aggregation — that is the moment the Intelligence context (§5.3) is
  born, and not before.

---

## 11. Decision Frameworks

### 11.1 Platform, Intelligence, or Product?

For any proposed capability, walk this in order — first "yes" wins:

1. **Does it encode business/domain judgment** (what is a good
   opportunity, who is an ICP, what to recommend)? → **Product.**
   Domain judgment never generalizes as cleanly as it seems.
2. **Does it learn from outcomes across time or across products**
   (calibration, regression trends, routing)? → **Intelligence** —
   *if the context exists.* If not, build it inside the product and
   mark it `# harvest-candidate: intelligence`.
3. **Would a second, unrelated product use it unchanged** — not
   "adapted," *unchanged*? → **Platform candidate.** Then apply the
   stamping test: has this shape appeared 3+ times? Harvest. Twice?
   Wait. Once? It's product code, full stop.
4. **Unsure?** → **Product.** Misplacing code in a product is cheap to
   fix (harvest later); misplacing it in the platform taxes every
   future venture. The default direction of error is always downward.

### 11.2 Adopt, build, or wait? (new external capability/tool)

- Adopt when it's commodity infrastructure with an exit path
  (swappable behind an interface — the `LLMProvider` rule).
- Build when it *is* the differentiation (our eval discipline, our
  honesty constraints, our stamping recipe).
- Wait when the trigger hasn't fired. Name the trigger in writing.

### 11.3 When to spend a milestone on consolidation vs. features

Run the post-feature review; consolidate when (a) the next feature
would stamp a fourth copy, (b) a known misplacement starts causing real
friction, or (c) the review finds a boundary violation the linter
missed. Otherwise keep shipping — consolidation without evidence is
just refactoring for comfort.

---

## 12. 10-Year Evolution

A map of triggers, not dates. Phases advance on evidence; nothing here
is a promise to add complexity on schedule.

**Horizon 1 — The Machine Proves Itself (now → OIP full pipeline).**
M13–M15 complete the discovery product. MX.1–MX.3 climb the autonomy
ladder. Exit: OIP runs scheduled, bounded-autonomy discovery and its
recommendations are trusted enough to bet a venture on.
*Architecture:* Phase 1 modular monolith throughout.

**Horizon 2 — The Second Venture (trigger: a "build" verdict the CEO
backs).** Repo → uv workspace; platform becomes a real SDK with its
first external consumer; prompt templates rehome; platform vs product
ADR split. The second venture is the platform's true test — expect a
consolidation milestone paying for every "would generalize, probably"
guess that didn't.
*Architecture:* Phase 2 (events/queues) only if scheduled multi-product
runs demonstrate the need.

**Horizon 3 — The Learning Studio (trigger: two products with outcome
data).** Intelligence context materializes: cross-product evals,
calibration from recorded outcomes, model routing from measured
cost/quality. Venture selection is now data-fed, self-improving.
*Org:* first dedicated Platform/Intelligence ownership split.

**Horizon 4 — Portfolio Scale (trigger: 3–5 operating ventures).**
Selective service extraction (Phase 3) only for components with
measured scaling or isolation needs. Multi-tenancy and billing become
platform capabilities. Pods per venture; CTO function governs seams
and ADRs, not code review of every line.

**Horizon 5 — The Studio as Product (trigger: outsiders ask for the
machine).** Optional and only if evidence demands: the platform +
lifecycle + learning system offered to external builders. This is a
*decision point*, not a destination — the honest default is that it
never fires.

**Standing assumption across all horizons:** model capability keeps
rising. Design consequence: keep agents thin (one responsibility, one
prompt, one schema) so a better model slots in behind `LLMProvider`
and evals immediately measure the uplift. Never build elaborate
scaffolding that compensates for a model weakness which the next
generation will erase — that scaffolding becomes dead weight with a
maintenance bill.

---

## 13. Architectural Guardrails (what engineers must never do)

The never-do list. Each is enforced by tooling where possible; where
not, by review.

1. Never let the Platform import a Product or Intelligence module
   (import-linter contract #4 — build fails).
2. Never let an agent import repositories or touch the DB (contract #2).
3. Never let the ORM cross a repository boundary in either direction —
   schemas in, schemas out.
4. Never create sessions or wire layers outside `runtime/` (ADR-0010;
   contract #3's one documented exception).
5. Never ship a prompt without eval fixtures (loader-enforced).
6. Never hardcode prompts, keys, model IDs, weights, or business rules.
7. Never do arithmetic, ranking, or thresholding inside a prompt that
   deterministic code could do (ADR-0012).
8. Never invent facts in an AI output path — honesty constraints are
   pinned by tests; removing one is an ADR-level event (ADR-0013).
9. Never add a platform abstraction ahead of the third stamping
   (ADR-0014/0015).
10. Never define workflow structure in config — no YAML DAGs, no
    config-driven orchestration, ever.
11. Never let one product import another product.
12. Never skip a rung on the autonomy ladder (HITL → HOTL → bounded).
13. Never add a top-level package without updating the import-linter
    contracts — they fail silently-permissive, so the update *is* the
    enforcement (known trade-off, recorded).
14. Never amend an ADR's history — supersede or append a correction.
15. Never lower a quality gate to make a milestone "done."

---

## 14. Success Metrics

Metrics per major capability. **Rule:** every metric must be computable
from durable stores (run logs, eval results, git history, outcome
records) — no vibes metrics. Targets are set per-horizon by the
decision loop (§10); v1.0 records the *measures*, which are stable.

| Capability | Success metrics |
|---|---|
| **Platform (frames/SDK)** | Time-to-walking-skeleton for a new venture (target direction: days, falling); % of new-stage code that is domain-only; frame-module churn per venture added (falling = frames are stable); zero seam violations reaching main |
| **Prompt & eval system** | Eval pass rate on main (100% — it's a gate); regressions caught pre-merge vs post-merge (all pre); model-upgrade eval diff turnaround; honesty-test count per agent (never decreasing) |
| **Discovery product (OIP)** | Pipeline E2E completion rate; cost per scored opportunity; % of "build" verdicts CEO judges credible on review; later: precision of build/watch/pass vs recorded outcomes |
| **Autonomy ladder (MX)** | Escalation rate (falling within a rung = ready for the next); budget-breach count (zero tolerated); human review turnaround; incidents caused by autonomous action (zero at each rung before promotion) |
| **Learning system** | Revisit-triggers fired and acted on per quarter; outcome records joined to predictions (coverage %); scoring calibration error trend across cycles |
| **Repository & org health** | Quality-gate pass rate on first attempt; consolidation-review cadence held; ADR coverage of non-obvious decisions (audited in the decision loop); milestone lead time trend |
| **Venture lifecycle** | Stage-gate cycle time per stage; salvage yield from sunsets (capabilities harvested + fixtures retained); portfolio decision hit-rate over rolling 2 years |

---

## 15. Explicit Anti-Patterns

Named so they can be called out in review by name.

1. **Premature microservices.** Extracting services for fashion. The
   monolith is a choice, not a phase to escape. (Phase 3 has entry
   criteria; "it would be cleaner" is not one.)
2. **Speculative platforming.** Building the abstraction before the
   third consumer. The most seductive failure mode for platform-minded
   engineers — it's why the third-stamping rule is non-negotiable #1.
3. **The config-driven workflow engine.** YAML DAGs, "no-code"
   pipeline builders, orchestration DSLs. Structure is code.
4. **Duplicated business logic.** The same domain rule living in two
   services or — worse — in a service *and* a prompt. One owner per
   rule; the service layer owns deterministic business math.
5. **Tightly coupled prompts.** Prompts that know about databases,
   other agents' outputs' quirks, or pipeline position. An agent gets
   a digest and returns a schema; everything else is the service's job.
6. **Prompt-side arithmetic.** Asking the model to compute weighted
   totals it will get subtly wrong. The LLM judges, the code computes.
7. **The genius agent.** One agent doing extraction + scoring +
   research "to save round trips." One responsibility, one prompt, one
   schema — always.
8. **Silent-permissive drift.** Adding packages/modules without
   updating enforcement contracts, so boundaries erode invisibly.
9. **Eval theater.** Fixtures so weak everything passes; evals written
   after the prompt "works." Fixtures ship in the same commit and
   encode the failure modes we actually fear (invented competitors,
   stale specifics).
10. **Autonomy leaps.** Shipping unattended agents because the demo
    behaved. The ladder exists because incidents at rung 3 are
    business-ending in a way rung-1 mistakes never are.
11. **The immortal deferral.** "Deferred" work with no named trigger,
    re-deferred forever. Every deferral names its trigger or it's a
    decision to *never* do it — say which.
12. **Rewriting history.** Editing old ADRs to look right in
    hindsight. The corpus's value *is* its honesty.
13. **Milestone smearing.** Half of M(n) sliding into M(n+1) with no
    record. Milestones end with all gates green or an explicit debt
    note — nothing in between.
14. **Model-weakness scaffolding.** Elaborate multi-step workarounds
    for a current model's limitation, built without an exit plan for
    when the next model makes them dead weight.

---

## 16. The CTO Critique

An operating manual that only praises its own system is eval theater.
Honest weaknesses of v1.0, with mitigations:

1. **N=1 evidence base.** Every "proven" pattern here is proven on one
   product, one domain, one developer-pair. The stamping recipe may be
   overfit to pipeline-shaped products; the first interactive or
   realtime venture will stress frames that have never seen a
   concurrent user. *Mitigation:* Horizon 2 explicitly budgets a
   consolidation milestone for the platform's first contact with a
   second domain; treat every §8 claim as a hypothesis until then.

2. **The funnel is unvalidated.** The studio's stage-1 gate is OIP's
   output, but no OIP recommendation has yet been tested against
   reality — the outcome loop (§10 loop 3) doesn't exist until MX.2.
   Until then, venture selection is CEO judgment wearing a
   data-flavored costume. *Mitigation:* say so out loud at every
   stage-1 gate; prioritize the outcome loop over pipeline breadth.

3. **Bus factor of one, twice over.** One human holds all business
   context; one AI lineage holds most engineering context, mitigated
   only by the ADR corpus and this manual. The docs-as-memory bet is
   good but untested by an actual cold-start contributor.
   *Mitigation:* periodically cold-start a fresh session/agent against
   the repo with zero conversational history and grade what it gets
   wrong; fix the docs, not the session.

4. **Honesty constraints are tested, honesty itself is not measured.**
   We pin prompt wording and check outputs against golden cases, but
   we don't yet measure real-world staleness or fabrication rates on
   live data. ADR-0013's trigger ("observed stale assessments")
   assumes we'd notice. *Mitigation:* MX.2's exception review must
   sample for staleness deliberately, not just wait for complaints.

5. **The manual could ossify.** Sixteen ADRs in two days is a
   high-metabolism phase; the risk inverts later — a thick rulebook
   that makes a small studio slow, rules enforced long after their
   evidence expired. *Mitigation:* the quarterly decision loop reviews
   the *manual* with the same skepticism the manual applies to code;
   every rule here should be traceable to an ADR or an incident, and
   any that isn't is a candidate for deletion.

6. **Cost is under-instrumented.** LLM spend appears nowhere in the
   quality gates and only thinly in §14. A 10-year studio of
   always-on agents lives and dies on unit economics. *Mitigation:*
   cost telemetry lands with `monitoring/` before MX.1 — treat
   "cost per pipeline run" as a first-class metric from the first
   scheduled run onward.

7. **Intelligence is the vaguest context — deliberately, but still.**
   §5.3 defers it correctly, but "we'll harvest it when it appears"
   has a failure mode: outcome data not *recorded now* can't be
   harvested later. *Mitigation:* the cheap insurance is durable
   run/outcome records starting immediately (they already exist as
   agent-run logs and score records); the expensive part — the
   learning machinery — stays deferred.

This critique is part of the manual so that v2.0 must answer it.

---

## Appendix A — Amendment Log

| Version | Date | Change | Authority |
|---|---|---|---|
| 1.0 | 2026-07-03 | Initial manual | CEO + CTO |
| 1.1 | 2026-07-03 | Roadmap v4 (revenue-first): R1–R3 milestones added; web-grounded research trigger fired; ICP postponed, company discovery cut, M15 absorbed by R3, MX postponed; consolidation rhythm paused until R3 | ADR-0017 (CEO decision) |
| 1.2 | 2026-07-03 | R1 (web-grounded competition research) shipped: capability map row flipped to ✅ | ADR-0018 |

## Appendix B — Source Evidence

Grounding for every claim marked "proven": ADR-0001 through ADR-0018
(`docs/architecture/`), milestones M0–M12 and R1 shipped behind the
full quality gate, and the enforcement configuration in `pyproject.toml`
(`[tool.importlinter]`). Where this manual and an ADR conflict, the
ADR is the historical record and this manual is the current policy —
file a correction against whichever is wrong.

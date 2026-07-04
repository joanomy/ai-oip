# ADR-0017: Roadmap v4 — Revenue-First Reordering

**Status:** Accepted
**Date:** 2026-07-03
**Milestone:** roadmap re-plan (supersedes the remaining-order portion of
ADR-0006's roadmap v3; CEO decision)

## Context

M12 closed the five-stage discovery pipeline (problems → workflows →
scores → landscapes → build/watch/pass). Roadmap v3's remaining order
was M13 → M14 → M15 → MX.1–MX.3 — all factory improvements. The CEO
asked for the shortest path from today's repository to the first
$1M ARR while preserving architecture quality.

The diagnosis: the repo has an excellent factory and no storefront.
Nothing in it today is something a stranger can pay for — but the
pipeline's own output, the report, is weeks (not milestones) away from
being sellable. The remaining v3 milestones mostly serve the studio's
internal venture funnel, not a paying customer.

## Decisions

### 1. First commercial product: the "AI Opportunity Briefing"

A recurring, vertical-specific intelligence report — the N most
buildable AI product opportunities in the customer's vertical, scored,
competition-mapped, with build/watch/pass verdicts — delivered as a
polished report, concierge-run by the CEO. Plus a one-off deep-dive
SKU. Productized service first, SaaS later: the commercial stack is a
Stripe payment link and email delivery. No login, no dashboard, no
multi-tenancy, no billing code. First ICP: AI development agencies and
consultancies (recurring budgeted need, founder-to-founder sales
cycle); venture studios secondary.

The honesty discipline (ADR-0013) is retained as a market
differentiator, not just an engineering value: the customer-facing
report keeps its grounding/knowledge-lag banner.

### 2. Roadmap v4: three revenue milestones, then a sales gate

R1 → R2 → R3, then **stop building and sell** (10 design-partner
conversations, 3 paid pilots) before any further engineering.

- **R1 — Web-grounded competition research.** ADR-0013's v2, behind
  the same interface. Gates sellability (see §3).
- **R2 — Collector breadth.** Two or three sources beyond Hacker News
  (Reddit, product-review sites, job postings) so a briefing can cover
  a customer's vertical rather than skewing dev-tools. Each is a small
  stamp of the `BaseCollector`/`CollectedItem` frame — this is what
  that frame was harvested for.
- **R3 — Report v2 (supersedes M15, promoted).** The report is the
  product, so it gets product-grade polish: branded HTML/PDF,
  methodology page, honesty banner, per-opportunity evidence links
  (enabled by R1/R2). Includes **cost-per-report telemetry** — the one
  slice of `monitoring/` built now, because pricing requires knowing
  unit economics (the operating manual's §16.6 critique, answered
  early).

### 3. ADR-0013's v2 trigger is declared fired — on commercial evidence

ADR-0013 set the web-grounding trigger as "stale assessments observed
on real runs" and budgeted it around MX. The commercial re-reading: a
customer paying for competitive intelligence will observe staleness in
the first ten minutes and churn — model-knowledge-only research is
fine for an internal funnel and disqualifying for a paid product. This
is the trigger firing, not the trigger being bypassed. Implementation
is exactly the upgrade path ADR-0013 reserved: `LLMProvider` grows
tool support, the prompt gets a v2, and the interface, schemas, and
storage don't change. (Confirmed feasible with zero new orchestration:
Anthropic web search is a server-side tool — declared in the request,
results and citations return in the same response.)

### 4. Postponed and cut

- **M13 (ICP generator): postponed as a pipeline stage.** The
  judgment ("who buys this") is valuable *report content* and may land
  inside R3's prompt/report rather than as a new stage + store.
  Revisit as a stage only if a customer workflow needs persisted ICPs.
- **M14 (company discovery): cut.** That is a lead-generation product
  in a market others already own; it takes no leverage from the
  differentiated asset (the opportunity pipeline). Reinstating it is a
  new-product decision (§6), not a backlog item.
- **MX.1–MX.3: postponed.** Autonomy saves founder hours, and founder
  hours are not the constraint — customers are. Concierge operation
  *is* human-in-the-loop, so rung 1 of the ladder is satisfied by the
  operating model itself. Trigger to revisit: ~20 paying subscribers,
  or weekly runs demonstrably straining the founder.
- **Consolidation-review rhythm: paused until R3 ships** — by the
  manual's own §11.3, consolidation with zero customers is refactoring
  for comfort. The post-R3 review is *committed*, not optional: R2
  stamps collectors #2–#4, prime harvest-review material.

### 5. Engineering discipline is unchanged

Quality gates, loader-enforced evals, the platform/domain seam,
one-milestone-at-a-time approval, and ADR discipline all hold for
R1–R3. This ADR reorders the roadmap; it does not lower any bar.

### 6. PMF evidence and the Product-#2 gate (recorded so the future
argument is with this document, not from scratch)

**PMF evidence:** 10 customers paying ≥$500/mo; ≥3 renewing past month
3 without discounting; ≥2 unprompted referrals; customers acting on
briefings and saying so; <5% of report claims flagged stale/wrong by
paying readers (the first real measurement of honesty in the wild —
manual §16.4).

**Product #2 gate:** not before $1M ARR on Product #1, unless (a)
growth stalls two consecutive quarters with churn — not sales
capacity — as the demonstrated cause, or (b) >30% of paying customers
independently pull for the same adjacent product; in either case only
with healthy logo retention. This is Horizon 2's trigger ("a build
verdict the CEO backs") with money as the backing.

## Consequences

- CLAUDE.md milestone table and execution order updated to v4; the
  operating manual is amended to v1.1 citing this ADR (its §3
  capability map rows for web-grounded research, ICP generation,
  company discovery, and report v2 change status).
- `ai-oip research` gains grounded assessments at R1 with no CLI or
  schema change visible to downstream stages.
- M15 ceases to exist as a numbered milestone; its scope lives in R3.
- Legacy numbering note: M13/M14/M15/MX references in ADRs 0006–0016
  remain historically accurate; interpret via this ADR.

## Revisit When

- The sales gate fails — 10 conversations yield no paid pilot: the
  product hypothesis (briefing, agency ICP, price point) is wrong;
  re-plan the *product*, don't add engineering.
- A pilot customer's usage demands self-serve (login, scheduling):
  that's MX.1's real trigger arriving with revenue attached.
- R1 in production shows the per-search/token cost making briefing
  unit economics untenable at target pricing: revisit grounding depth
  (searches per assessment) before revisiting price.

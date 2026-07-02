# ADR-0002: Modular Monolith Layering, Enforcement, and Project Naming

**Status:** Accepted (layer order in Decision 2 superseded in part by ADR-0004 — `logging`/`monitoring` now depend on `config`)
**Date:** 2026-07-02
**Milestone:** M1 — Project Architecture & Folder Structure

## Context
Before any concrete agent, pipeline, or business logic is written, the
package boundaries and their allowed dependency directions need to be
fixed — and, critically, enforced by tooling rather than left as a
convention that erodes as the codebase grows.

Separately, the project was renamed during this milestone:
`ai_platform` → `ai_iop`. Recorded here so the history is traceable from
the ADR log rather than only from git commit messages.

## Decisions

### 1. Package name: `ai_iop`
Reflects the product identity: AI Opportunity Intelligence Platform.
Renaming this early (before any consumer code exists) cost a mechanical
rename pass; renaming after M4+ would have cost a migration.

**Correction (post-M4 engineering review):** this section originally
claimed the milestone renamed the package all the way to `ai_oip` and
that naming was "finalized before the database layer." Both claims were
wrong. The actual M1 commit (`c0aae81`) renamed `ai_platform` → `ai_iop`
only. The acronym-order correction to `ai_oip` did not happen until
**M4**, during the database layer itself — see ADR-0005. This ADR is
left otherwise unedited per the project's ADR-as-historical-record
convention (see ADR-0001's addendum for the same pattern); this note
exists so a reader trusts the corrected fact, not the original claim.

### 2. Ten-package layered structure
```
pipelines → services → collectors, agents → repositories → models → schemas, prompts → config, logging, monitoring → core
```
Each arrow means "depends on, never the reverse." `core` sits at the
foundation with zero internal dependencies; everything may depend on it.

### 3. Repository pattern (`repositories/` owns all DB access)
`agents/`, `services/`, and `pipelines/` never import `models/` or hold
a database session directly. Only `repositories/` does. This is what
lets the database technology change later without touching business
logic or agent code.

### 4. Agents never import repositories (hard rule)
An agent's contract is "typed input in, typed output out." If an agent
needs data, a `service` fetches it and passes it in via the input
schema. This keeps every agent:
- Testable with zero database dependency
- Swappable (different LLM provider, different prompt version) without
  touching anything that talks to the database
- Safe to run inside an autonomous pipeline without hidden side effects

### 5. Enforcement via `import-linter`, not documentation alone
A folder structure and a paragraph in a README do not stop someone from
importing across a boundary under deadline pressure. `import-linter` is
wired into `pyproject.toml` with two contracts:
- **Layered architecture**: enforces the full dependency chain above
- **Agents never import repositories**: the single rule most likely to
  be violated by accident, called out explicitly

Both contracts run in CI (`.github/workflows/ci.yml`) on every push.
Verified during this milestone by deliberately introducing a violating
import and confirming `lint-imports` catches it with the exact file and
line — see M1 conversation record for the reproduction.

### 6. `models/` vs `schemas/` kept separate
`models/` (SQLAlchemy, data at rest) and `schemas/` (Pydantic, data in
motion) are not merged into one class per entity. Costs a small amount
of mapping code now; avoids being unable to change an agent's output
shape without a database migration later.

## Consequences
- Every future PR must pass `lint-imports` in addition to ruff/mypy/pytest.
- Adding a new package to `src/ai_oip/` requires adding it to the
  `layers` list in `pyproject.toml`, or import-linter will not know
  where it belongs in the hierarchy (fails safe: unrecognized modules
  are simply not covered by the layer contract, so this should be done
  deliberately at the time a new package is introduced).
- `BaseAgent` and `BaseRepository` are now stable interfaces. Changing
  their method signatures after M6 (agents) and M4 (database) exist
  will require updating every concrete implementation — worth getting
  the interface right now rather than after adoption.

## Revisit When
- A package's dependencies genuinely don't fit the linear layer model
  (e.g., a cross-cutting concern). Add a named exception to the
  contract rather than removing enforcement.
- Extraction into an independent service (Phase 3 per architecture
  evolution strategy) — the layer boundaries here are exactly the
  candidate seams for that extraction.

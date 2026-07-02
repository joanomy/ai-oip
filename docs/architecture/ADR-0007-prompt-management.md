# ADR-0007: Prompt Management

**Status:** Accepted
**Date:** 2026-07-02
**Milestone:** M4 — Prompt Management

## Context

Every agent's contract requires its prompt to exist as a versioned,
external template (CLAUDE.md, Agent Design / Prompt Management) — this
is why M4 executes before the agent framework (M3). ADR-0006 adds the
eval discipline: every prompt ships with eval fixtures the M3 harness
will consume. This milestone builds the storage format, the loader,
and the fixture convention. No production prompts exist yet — they
arrive with the business milestones (M8+); tests use a DemoRecord-style
fixture prompt.

## Decisions

### 1. Format: Markdown files, YAML frontmatter, Jinja2 body

One directory per prompt, one file per version (`v1.md`, `v2.md`),
fixtures alongside (`evals/cases.yaml`). Frontmatter carries exactly
the fields CLAUDE.md mandates for every prompt: `name`, `version`,
`outcome`, `role`, `objective`, `input_schema`, `output_schema`,
`validation_rules` — validated by a Pydantic model (`extra="forbid"`),
so a typo'd or missing field fails at load, not at render.

Alternatives rejected: pure YAML/JSON (hostile to multi-paragraph
prose); Python modules (prompts-as-code violates "external to code");
a database (versioning belongs in git where diffs are reviewable).

### 2. Jinja2 with StrictUndefined, plus an explicit variable-set check

`str.format` was rejected because prompt bodies routinely contain JSON
examples — `{"greeting": ...}` — whose braces `format()` treats as
placeholders. Jinja2's `{{ var }}` syntax leaves single braces alone.
`StrictUndefined` is defense in depth; the primary check is explicit:
`render()` compares provided variables against the template's declared
set and rejects both missing *and* unexpected names
(`PromptRenderError`). A prompt silently ignoring a variable it wasn't
written for is quiet drift that produces bad agent output with no
traceable cause.

Templates are trusted, version-controlled repo files — only variables
are runtime data — so a sandboxed Jinja environment is unnecessary.
`autoescape=False` because these are text prompts, not HTML.

### 3. Frontmatter must agree with its location

`name` must match the directory, `version` must match the filename;
disagreement is a `PromptError`. Two sources of truth that can drift
are how the package-rename history got misrecorded in ADR-0002 —
cheaper to make drift impossible than to audit for it.

### 4. Schemas referenced by name, not imported

`input_schema`/`output_schema` are strings. `prompts/` sits at the
same layer as `schemas/` (neither may import the other; both depend
only on `core`), so binding a schema name to a Pydantic class is the
agent layer's job (M3) — agents may import both. This keeps the layer
contract intact with zero exceptions.

### 5. Eval fixtures are required, and absence is an error

`load_eval_cases()` raises `PromptNotFoundError` for a missing
fixtures file and `PromptError` for an empty list — never a silent
`[]`. ADR-0006's gate is "no agent ships without an eval suite"; an
API that returns an empty suite for a missing file would let that gate
pass vacuously. `PromptEvalCase.expected` is deliberately loose
(`dict`) at this milestone: the M3 runner defines its assertion
semantics. What M4 verifies by test: fixtures parse, and their
variables actually render against the template they belong to.

### 6. Production templates packaged with the wheel

`src/ai_oip/prompts/templates/` (empty but for `.gitkeep` until M8+)
ships inside the package; `PromptLoader` defaults to it and takes a
`base_path` override for tests. New runtime deps: `jinja2`, `pyyaml`
(+ `types-pyyaml` in dev for mypy strict).

## Consequences

- Adding a prompt = adding a directory with `v1.md` + `evals/cases.yaml`;
  no code changes. Changing a prompt = adding `v<N+1>.md` beside the old
  version — history stays reviewable in git.
- `PromptError` / `PromptNotFoundError` / `PromptRenderError` join the
  `AIOIPError` hierarchy, so pipelines can categorize prompt failures
  separately from agent-execution and repository failures.
- The M3 eval runner has a stable fixture contract to build against.

## Revisit When

- M3 (Agent Framework & Evaluation Harness): formalize
  `PromptEvalCase.expected` semantics; decide whether schema-name
  binding gets registry support.
- A prompt needs conditionals/loops in its body: Jinja2 supports them,
  but treat that as a design smell first — logic belongs in agents or
  services, not templates.
- Prompt count grows past ~10–15: introduce domain subdirectories
  (mirroring the planned `agents/` sub-namespacing).

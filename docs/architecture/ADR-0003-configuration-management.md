# ADR-0003: Configuration Management

**Status:** Accepted
**Date:** 2026-07-02
**Milestone:** M2 — Configuration Management

## Context
Every module in the platform eventually needs environment-dependent
values (deployment environment, log level, and later: database URLs,
LLM provider API keys). Left unmanaged, `os.environ.get(...)` calls
spread across the codebase, config validation happens implicitly at
first use (often deep in a call stack, often in production), and no
single place documents what configuration the application actually
needs to run.

## Decisions

### 1. `pydantic-settings.BaseSettings`, not raw `os.environ`
Gives typed, validated configuration for free. A missing or malformed
required value is a `ValidationError` at `Settings()` instantiation
time, not a `KeyError` or silent `None` three modules away at 3am.

### 2. Single cached factory: `get_settings()`
A `functools.lru_cache`-wrapped factory instead of a module-level
constant. Production gets effectively-singleton behavior (parsed once,
`.env`/environment read once). Tests get `get_settings.cache_clear()`
to reload configuration under different environment variables without
import-time side effects leaking between test cases.

### 3. `os.environ`/`os.getenv` banned outside `config/`
Enforced via `ruff`'s `TID251` banned-api rule
(`[tool.ruff.lint.flake8-tidy-imports.banned-api]` in `pyproject.toml`),
not left as a convention. Verified during this milestone by
deliberately writing a violating file and confirming `ruff check`
rejects it with a message pointing to `get_settings()` — see M2
conversation record.

### 4. `debug=True` + `environment=production` is a validation error
A `model_validator` on `Settings` raises rather than allowing this
combination. Debug mode typically means verbose error output; shipping
that to production users is a real, not theoretical, risk. Enforcing
it as a startup failure means the mistake is caught in CI/deploy, not
discovered from a leaked stack trace in production.

### 5. Fields added now: `environment`, `app_name`, `app_version`,
`log_level`, `debug`. Deliberately NOT added yet: database URL (waits
for M4), LLM provider API keys (waits for M6). Adding speculative
config for capabilities that don't exist yet violates "simplest
architecture that satisfies current requirements" — `Settings` is
designed to grow by addition, not rewrite, so this costs nothing later.

## Consequences
- Every future module that needs configuration takes it as an explicit
  constructor/function argument (typically `settings: Settings`),
  never by importing `os` itself.
- Adding a new setting means: add the field to `Settings`, document it
  in `.env.example`, and (if it's the kind of value that shouldn't be
  logged) consider `pydantic.SecretStr` — a pattern to establish
  concretely when the first API key field is added in M6.
- `get_settings()` being cached means tests that mutate environment
  variables must call `get_settings.cache_clear()` before and,
  ideally, after (via a fixture) to avoid leaking state into other
  tests. Worth a shared pytest fixture once more than a few tests need
  this — noted as a Future Improvement rather than built now.

## Revisit When
- The first secret (API key) is added — decide then whether
  `SecretStr` masking in logs/repr is sufficient or whether a secrets
  manager integration (e.g., AWS Secrets Manager, Vault) is warranted.
  Not needed yet; env vars are sufficient at this stage.
- Multiple services eventually need to share configuration — at that
  point, consider whether `Settings` needs to be split per-service or
  remain centralized.

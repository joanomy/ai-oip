"""Application settings: the single source of truth for all configuration.

This is the ONLY module in the codebase permitted to read from the
process environment (enforced by the `TID251` ruff rule — see
pyproject.toml `[tool.ruff.lint.flake8-tidy-imports.banned-api]`).
Every other module receives configuration values as explicit function
or constructor arguments, never by reaching into `os.environ` itself.

Usage:
    from ai_iop.config import get_settings

    settings = get_settings()
    if settings.is_production:
        ...
"""

from enum import StrEnum
from functools import lru_cache

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(StrEnum):
    """Deployment environment. Controls environment-specific defaults."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    """Typed, validated application configuration.

    Values are loaded from (in order of precedence, highest first):
    1. Explicit constructor arguments (mainly used in tests)
    2. Environment variables
    3. A `.env` file in the project root, if present
    4. The field defaults declared below

    Instantiating this class with missing/invalid required values raises
    `pydantic.ValidationError` immediately — configuration errors are a
    startup failure, not a runtime surprise.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    environment: Environment = Field(
        default=Environment.DEVELOPMENT,
        description="Deployment environment. Drives environment-specific defaults.",
    )
    app_name: str = Field(
        default="AI-IOP",
        description="Human-readable application name, used in logs and health checks.",
    )
    app_version: str = Field(
        default="0.0.1",
        description="Application version, surfaced in health checks and logs.",
    )
    log_level: str = Field(
        default="INFO",
        description="Python logging level name (DEBUG, INFO, WARNING, ERROR).",
    )
    debug: bool = Field(
        default=False,
        description="Enables verbose/debug behavior. Must be False in production.",
    )

    @property
    def is_production(self) -> bool:
        """True if running in the production environment."""
        return self.environment is Environment.PRODUCTION

    @property
    def is_development(self) -> bool:
        """True if running in the development environment."""
        return self.environment is Environment.DEVELOPMENT

    @model_validator(mode="after")
    def _forbid_debug_in_production(self) -> "Settings":
        """Fail startup rather than silently run production with debug on.

        Debug mode typically enables verbose error output, which can leak
        stack traces or internal state to end users if turned on in
        production. This is enforced as a validation error rather than a
        code review reminder.
        """
        if self.is_production and self.debug:
            raise ValueError("debug must be False when environment=production")
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached, process-wide Settings instance.

    Cached so `.env`/environment parsing and validation happens exactly
    once per process, not on every call site. Tests that need different
    configuration should call `get_settings.cache_clear()` first.
    """
    return Settings()

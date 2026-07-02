"""Structured logging configuration and access.

Centralizes logging setup so it happens exactly once, driven entirely
by `Settings`, rather than being configured ad hoc by whichever module
happens to log first. Every module that needs a logger calls
`get_logger(__name__)` — nothing configures `structlog` or the stdlib
`logging` module directly outside this file.
"""

import logging as stdlib_logging
import sys
from typing import cast

import structlog
from structlog.typing import FilteringBoundLogger, Processor

from ai_oip.config import Settings

_configured = False


def _resolve_level(log_level: str) -> int:
    """Convert a level name (e.g. 'INFO') into its numeric logging value.

    Raises:
        ValueError: if `log_level` is not a recognized level name.
    """
    level = stdlib_logging.getLevelName(log_level.upper())
    if not isinstance(level, int):
        raise ValueError(f"Unknown log level: {log_level!r}")
    return level


def configure_logging(settings: Settings) -> None:
    """Configure structlog for the whole process. Call once at startup.

    Rendering depends on environment:
        - development: human-readable, colorized console output
        - staging / production: single-line JSON, safe to ship to a
          log aggregator and query on structured fields

    Idempotent in the sense that calling it again fully replaces the
    prior configuration (useful for tests via `reset_logging()`).
    """
    global _configured

    level = _resolve_level(settings.log_level)

    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    renderer: Processor = (
        structlog.dev.ConsoleRenderer()
        if settings.is_development
        else structlog.processors.JSONRenderer()
    )

    structlog.configure(
        processors=[*shared_processors, renderer],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )
    _configured = True


def reset_logging() -> None:
    """Reset structlog to its unconfigured default state. Test-only.

    Ensures one test's `configure_logging()` call can't leak into the
    next test's assertions about rendering or level filtering.
    """
    global _configured
    structlog.reset_defaults()
    _configured = False


def is_configured() -> bool:
    """True if `configure_logging()` has been called and not since reset."""
    return _configured


def get_logger(name: str | None = None) -> FilteringBoundLogger:
    """Return a structured logger, optionally bound to a component name.

    Convention: call as `get_logger(__name__)` so log output identifies
    which module emitted it.

    Safe to call before `configure_logging()` runs — structlog falls
    back to its own defaults until configured — but application code
    should call `configure_logging()` at process startup before any
    meaningful log volume is produced.
    """
    return cast(FilteringBoundLogger, structlog.get_logger(name))

"""Logging: structured logging setup.

Dependency rule: depends on config, core. Nothing outside this package
configures structlog or the stdlib logging module directly — every
module gets a logger via `get_logger(__name__)`.
"""

from ai_oip.logging.config import configure_logging, get_logger, is_configured, reset_logging

__all__ = ["configure_logging", "get_logger", "is_configured", "reset_logging"]

"""Shared exception types.

Every layer raises from this hierarchy rather than bare Exception, so
callers (especially pipelines running autonomously) can catch failures
by category and decide whether to retry, skip, or halt.
"""


class AIIOPError(Exception):
    """Base exception for all AI-IOP errors."""


class AgentExecutionError(AIIOPError):
    """Raised when an agent fails during `run`.

    Wraps the underlying cause so agent failures are distinguishable
    from infrastructure failures (DB, network) further up the stack.
    """

    def __init__(self, agent_name: str, message: str) -> None:
        self.agent_name = agent_name
        super().__init__(f"[{agent_name}] {message}")


class RepositoryError(AIIOPError):
    """Raised when a data access operation fails."""


class ConfigurationError(AIIOPError):
    """Raised when required configuration is missing or invalid."""

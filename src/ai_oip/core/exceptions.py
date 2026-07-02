"""Shared exception types.

Every layer raises from this hierarchy rather than bare Exception, so
callers (especially pipelines running autonomously) can catch failures
by category and decide whether to retry, skip, or halt.
"""


class AIOIPError(Exception):
    """Base exception for all AI-OIP errors."""


class AgentExecutionError(AIOIPError):
    """Raised when an agent fails during `run`.

    Wraps the underlying cause so agent failures are distinguishable
    from infrastructure failures (DB, network) further up the stack.
    """

    def __init__(self, agent_name: str, message: str) -> None:
        self.agent_name = agent_name
        super().__init__(f"[{agent_name}] {message}")


class RepositoryError(AIOIPError):
    """Raised when a data access operation fails."""


class PromptError(AIOIPError):
    """Raised when a prompt template is malformed or fails validation."""


class PromptNotFoundError(PromptError):
    """Raised when a prompt, version, or its eval fixtures don't exist."""


class PromptRenderError(PromptError):
    """Raised when rendering is attempted with wrong variables.

    Missing and unexpected variables are both errors — a prompt silently
    rendering without a variable it declares (or ignoring one it wasn't
    written for) is exactly the kind of quiet drift that produces bad
    agent output with no traceable cause.
    """


class ConfigurationError(AIOIPError):
    """Raised when required configuration is missing or invalid."""


class ProviderError(AIOIPError):
    """Raised when an LLM provider call fails (network, rate limit, API error).

    Distinct from AgentExecutionError so pipelines can tell "the model
    couldn't be reached" (often retryable) apart from "the agent produced
    bad output" (usually not retryable as-is).
    """


class EvalError(AIOIPError):
    """Raised when an eval fixture is malformed or uses unknown expectation types.

    A *failing* eval case is a result, not an exception — this is raised
    only when the eval itself cannot be run as written.
    """

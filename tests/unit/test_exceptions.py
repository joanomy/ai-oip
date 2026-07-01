"""Unit tests for the shared exception hierarchy."""

from ai_iop.core.exceptions import (
    AgentExecutionError,
    AIIOPError,
    ConfigurationError,
    RepositoryError,
)


def test_agent_execution_error_includes_agent_name_in_message() -> None:
    error = AgentExecutionError(agent_name="summarizer", message="LLM timeout")

    assert error.agent_name == "summarizer"
    assert "summarizer" in str(error)
    assert "LLM timeout" in str(error)


def test_all_domain_errors_are_aios_errors() -> None:
    assert issubclass(AgentExecutionError, AIIOPError)
    assert issubclass(RepositoryError, AIIOPError)
    assert issubclass(ConfigurationError, AIIOPError)

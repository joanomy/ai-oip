"""Tests for the agent framework helpers: registry, output guardrail, tracing."""

import pytest
import structlog
from pydantic import BaseModel

from ai_oip.agents import AgentRegistry, BaseAgent, log_agent_run, parse_json_output
from ai_oip.core.exceptions import AgentExecutionError


class GreetingInput(BaseModel):
    person_name: str


class GreetingOutput(BaseModel):
    greeting: str


class GreeterAgent(BaseAgent[GreetingInput, GreetingOutput]):
    name = "greeter"

    async def run(self, input_data: GreetingInput) -> GreetingOutput:
        return GreetingOutput(greeting=f"Hello {input_data.person_name}")


class TestRegistry:
    def test_register_and_get_roundtrip(self) -> None:
        registry = AgentRegistry()

        registry.register(GreeterAgent)

        assert registry.get("greeter") is GreeterAgent
        assert registry.names() == ["greeter"]

    def test_register_works_as_decorator(self) -> None:
        registry = AgentRegistry()

        returned = registry.register(GreeterAgent)

        assert returned is GreeterAgent

    def test_duplicate_name_is_rejected(self) -> None:
        registry = AgentRegistry()
        registry.register(GreeterAgent)

        with pytest.raises(ValueError, match="already registered"):
            registry.register(GreeterAgent)

    def test_class_without_name_is_rejected(self) -> None:
        registry = AgentRegistry()

        class NamelessAgent(BaseAgent[GreetingInput, GreetingOutput]):
            async def run(self, input_data: GreetingInput) -> GreetingOutput:
                raise NotImplementedError

        with pytest.raises(ValueError, match="non-empty `name`"):
            registry.register(NamelessAgent)

    def test_unknown_name_raises_with_available_names(self) -> None:
        registry = AgentRegistry()
        registry.register(GreeterAgent)

        with pytest.raises(KeyError, match="greeter"):
            registry.get("does_not_exist")


class TestOutputGuardrail:
    def test_plain_json_parses_into_schema(self) -> None:
        result = parse_json_output(
            '{"greeting": "Hello Ada"}', GreetingOutput, agent_name="greeter"
        )

        assert result.greeting == "Hello Ada"

    def test_markdown_fenced_json_is_tolerated(self) -> None:
        raw = '```json\n{"greeting": "Hello Ada"}\n```'

        result = parse_json_output(raw, GreetingOutput, agent_name="greeter")

        assert result.greeting == "Hello Ada"

    def test_fence_without_language_tag_is_tolerated(self) -> None:
        raw = '```\n{"greeting": "Hi"}\n```'

        result = parse_json_output(raw, GreetingOutput, agent_name="greeter")

        assert result.greeting == "Hi"

    def test_invalid_json_raises_agent_execution_error(self) -> None:
        with pytest.raises(AgentExecutionError, match="not valid JSON"):
            parse_json_output("not json at all", GreetingOutput, agent_name="greeter")

    def test_schema_mismatch_raises_agent_execution_error(self) -> None:
        with pytest.raises(AgentExecutionError, match="does not match GreetingOutput"):
            parse_json_output('{"wrong": 1}', GreetingOutput, agent_name="greeter")

    def test_error_message_carries_agent_name(self) -> None:
        with pytest.raises(AgentExecutionError, match=r"\[greeter\]"):
            parse_json_output("{", GreetingOutput, agent_name="greeter")


class TestTracing:
    def test_successful_run_logs_start_and_complete_with_duration(self) -> None:
        with structlog.testing.capture_logs() as captured, log_agent_run("greeter"):
            pass

        events = [(entry["event"], entry["agent_name"]) for entry in captured]
        assert events == [
            ("agent_run_started", "greeter"),
            ("agent_run_completed", "greeter"),
        ]
        assert captured[1]["duration_ms"] >= 0

    def test_failing_run_logs_failure_and_reraises(self) -> None:
        with (
            structlog.testing.capture_logs() as captured,
            pytest.raises(RuntimeError, match="boom"),
            log_agent_run("greeter"),
        ):
            raise RuntimeError("boom")

        assert captured[-1]["event"] == "agent_run_failed"
        assert captured[-1]["agent_name"] == "greeter"
        assert captured[-1]["duration_ms"] >= 0

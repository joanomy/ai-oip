"""Unit tests for the BaseAgent contract (Milestone 1).

Uses a minimal dummy agent to prove the abstract interface behaves as
intended: cannot be instantiated directly, and a valid subclass runs
with typed input/output.
"""

import pytest
from pydantic import BaseModel

from ai_iop.agents.base import BaseAgent


class _EchoInput(BaseModel):
    text: str


class _EchoOutput(BaseModel):
    text: str
    length: int


class _EchoAgent(BaseAgent[_EchoInput, _EchoOutput]):
    """Minimal test-only agent: one responsibility (echo + measure)."""

    name = "echo_agent"

    async def run(self, input_data: _EchoInput) -> _EchoOutput:
        return _EchoOutput(text=input_data.text, length=len(input_data.text))


def test_base_agent_cannot_be_instantiated_directly() -> None:
    with pytest.raises(TypeError):
        BaseAgent()  # type: ignore[abstract]


async def test_concrete_agent_runs_with_typed_io() -> None:
    agent = _EchoAgent()
    result = await agent.run(_EchoInput(text="hello"))

    assert result.text == "hello"
    assert result.length == 5


async def test_agent_output_is_validated_pydantic_model() -> None:
    agent = _EchoAgent()
    result = await agent.run(_EchoInput(text="hi"))

    assert isinstance(result, BaseModel)
    assert result.model_dump() == {"text": "hi", "length": 2}

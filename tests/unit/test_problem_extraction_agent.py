"""Tests for the Problem Extraction agent — including the packaged
production prompt and its eval fixtures running through the harness."""

import json

import pytest

from ai_oip.agents.problem_extraction import ProblemExtractionAgent
from ai_oip.core.exceptions import AgentExecutionError
from ai_oip.evals import prompt_completion_target, run_eval_cases
from ai_oip.prompts import PromptLoader
from ai_oip.schemas import ProblemExtractionInput
from tests.fixtures.fakes import FakeProvider, make_item

pytestmark = pytest.mark.asyncio

VALID_OUTPUT = json.dumps(
    {
        "problems": [
            {
                "description": "Manual invoice copying eats two hours weekly.",
                "context": "Small-business back office",
                "evidence": "I spend every Friday manually copying invoice data",
                "source_index": 1,
            }
        ]
    }
)


@pytest.fixture
def prompt():
    # The real packaged production prompt — default loader path.
    return PromptLoader().load("extract_problems")


async def test_packaged_prompt_loads_with_expected_contract(prompt) -> None:
    assert prompt.metadata.name == "extract_problems"
    assert prompt.metadata.version == 1
    assert prompt.metadata.input_schema == "ProblemExtractionInput"
    assert prompt.metadata.output_schema == "ProblemExtractionOutput"
    assert prompt.variables == {"items_digest"}


async def test_run_renders_digest_and_parses_output(prompt) -> None:
    provider = FakeProvider(VALID_OUTPUT)
    agent = ProblemExtractionAgent(provider=provider, prompt=prompt)

    output = await agent.run(ProblemExtractionInput(items=[make_item(1), make_item(2)]))

    assert len(output.problems) == 1
    assert output.problems[0].source_index == 1

    request = provider.requests[0]
    assert request.system == prompt.metadata.role
    assert "[1] Ask HN: item 1" in request.prompt
    assert "[2] Ask HN: item 2" in request.prompt
    assert '{"problems"' in request.prompt  # JSON shape survived Jinja


async def test_long_item_text_is_truncated_in_digest(prompt) -> None:
    provider = FakeProvider(VALID_OUTPUT)
    agent = ProblemExtractionAgent(provider=provider, prompt=prompt)
    long_item = make_item(1, text="x" * 5000)

    await agent.run(ProblemExtractionInput(items=[long_item]))

    assert "…[truncated]" in provider.requests[0].prompt
    assert "x" * 5000 not in provider.requests[0].prompt


async def test_fenced_json_output_is_tolerated(prompt) -> None:
    provider = FakeProvider(f"```json\n{VALID_OUTPUT}\n```")
    agent = ProblemExtractionAgent(provider=provider, prompt=prompt)

    output = await agent.run(ProblemExtractionInput(items=[make_item()]))

    assert len(output.problems) == 1


async def test_non_json_output_raises_agent_execution_error(prompt) -> None:
    provider = FakeProvider("Sorry, I cannot help with that.")
    agent = ProblemExtractionAgent(provider=provider, prompt=prompt)

    with pytest.raises(AgentExecutionError, match=r"\[problem_extraction\]"):
        await agent.run(ProblemExtractionInput(items=[make_item()]))


async def test_eval_fixtures_run_through_the_harness(prompt) -> None:
    """ADR-0006's gate, exercised on the first production prompt: the
    shipped fixtures load, render, complete, and evaluate."""
    cases = PromptLoader().load_eval_cases("extract_problems")
    target = prompt_completion_target(prompt, FakeProvider('{"problems": []}'))

    report = await run_eval_cases(target, cases)

    assert report.passed is True
    assert len(report.results) == 2

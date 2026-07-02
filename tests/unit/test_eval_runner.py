"""Tests for the eval runner — including an end-to-end pass over the
committed demo_greeting fixtures, closing the loop the prompt-management
milestone opened (fixtures parse AND are actually evaluable)."""

from pathlib import Path

import pytest

from ai_oip.core.exceptions import EvalError
from ai_oip.evals import EvalReport, run_eval_cases
from ai_oip.prompts import PromptEvalCase, PromptLoader

pytestmark = pytest.mark.asyncio

FIXTURES = Path(__file__).parent.parent / "fixtures" / "prompts"


def _case(case_id: str, expected: dict[str, object]) -> PromptEvalCase:
    return PromptEvalCase(id=case_id, variables={"person_name": "Ada"}, expected=expected)


async def _echo_target(variables: dict[str, object]) -> str:
    return f"Hello {variables['person_name']}!"


class TestExpectations:
    async def test_contains_passes_and_fails(self) -> None:
        report = await run_eval_cases(
            _echo_target,
            [_case("hit", {"contains": "Ada"}), _case("miss", {"contains": "Grace"})],
        )

        assert [r.passed for r in report.results] == [True, False]
        assert report.results[1].failures == ["expected output to contain 'Grace'"]
        assert report.passed is False
        assert report.pass_rate == 0.5

    async def test_not_contains(self) -> None:
        report = await run_eval_cases(
            _echo_target,
            [_case("ok", {"not_contains": "Grace"}), _case("bad", {"not_contains": "Ada"})],
        )

        assert [r.passed for r in report.results] == [True, False]

    async def test_matches_regex(self) -> None:
        report = await run_eval_cases(
            _echo_target,
            [_case("ok", {"matches": r"^Hello \w+!$"}), _case("bad", {"matches": r"^\d+$"})],
        )

        assert [r.passed for r in report.results] == [True, False]

    async def test_multiple_expectations_must_all_hold(self) -> None:
        report = await run_eval_cases(
            _echo_target,
            [_case("both", {"contains": "Ada", "not_contains": "Ada"})],
        )

        assert report.results[0].passed is False
        assert len(report.results[0].failures) == 1

    async def test_unknown_expectation_type_raises(self) -> None:
        with pytest.raises(EvalError, match="unknown expectation type 'sentiment'"):
            await run_eval_cases(_echo_target, [_case("bad", {"sentiment": "positive"})])

    async def test_non_string_expectation_value_raises(self) -> None:
        with pytest.raises(EvalError, match="must be a string"):
            await run_eval_cases(_echo_target, [_case("bad", {"contains": 42})])

    async def test_empty_report_has_zero_pass_rate(self) -> None:
        report = await run_eval_cases(_echo_target, [])

        assert isinstance(report, EvalReport)
        assert report.pass_rate == 0.0
        assert report.passed is True  # vacuously — the gate is on fixture existence


class TestEndToEndWithCommittedFixtures:
    async def test_demo_greeting_fixtures_run_through_the_harness(self) -> None:
        """The full ADR-0006 loop: load prompt + fixtures, render, evaluate."""
        loader = PromptLoader(base_path=FIXTURES)
        prompt = loader.load("demo_greeting")
        cases = loader.load_eval_cases("demo_greeting")

        async def render_target(variables: dict[str, object]) -> str:
            # Stand-in for a real agent: the rendered prompt itself is
            # the "output" — enough to prove fixtures are evaluable
            # end-to-end without a live model.
            return prompt.render(**variables)

        report = await run_eval_cases(render_target, cases)

        assert report.passed is True
        assert len(report.results) == 2

"""Eval runner: execute golden cases against a prompt-driven callable.

This gives `PromptEvalCase.expected` (deliberately loose since the
prompt-management milestone) its semantics. Supported expectation keys:

    contains:     str — output must contain this substring
    not_contains: str — output must NOT contain this substring
    matches:      str — output must match this regex (re.search)

A case may combine several keys; all must hold. Unknown keys or
non-string values raise `EvalError` — a mistyped fixture must fail
loudly, not silently pass as an empty check (same reasoning as the
prompt loader refusing missing fixtures, ADR-0006).

The runner evaluates a `(variables) -> awaitable str` callable rather
than a BaseAgent, so it needs no knowledge of any agent's input schema —
the thin adapter from agent to callable is written where the agent is
(services or the eval entrypoint), keeping this layer generic.
"""

import re
from collections.abc import Awaitable, Callable, Sequence

from pydantic import BaseModel, ConfigDict

from ai_oip.core.exceptions import EvalError
from ai_oip.prompts import PromptEvalCase

EvalTarget = Callable[[dict[str, object]], Awaitable[str]]


class EvalCaseResult(BaseModel):
    """Outcome of one eval case: passed, or failed with reasons."""

    model_config = ConfigDict(frozen=True)

    case_id: str
    passed: bool
    failures: list[str]


class EvalReport(BaseModel):
    """Aggregate outcome of an eval run."""

    model_config = ConfigDict(frozen=True)

    results: list[EvalCaseResult]

    @property
    def passed(self) -> bool:
        return all(result.passed for result in self.results)

    @property
    def pass_rate(self) -> float:
        if not self.results:
            return 0.0
        return sum(1 for result in self.results if result.passed) / len(self.results)


def _check_expected(output: str, expected: dict[str, object], case_id: str) -> list[str]:
    failures: list[str] = []
    for key, value in expected.items():
        if not isinstance(value, str):
            raise EvalError(
                f"Eval case {case_id!r}: expected[{key!r}] must be a string, "
                f"got {type(value).__name__}"
            )
        if key == "contains":
            if value not in output:
                failures.append(f"expected output to contain {value!r}")
        elif key == "not_contains":
            if value in output:
                failures.append(f"expected output to NOT contain {value!r}")
        elif key == "matches":
            if re.search(value, output) is None:
                failures.append(f"expected output to match /{value}/")
        else:
            raise EvalError(
                f"Eval case {case_id!r}: unknown expectation type {key!r} "
                "(supported: contains, not_contains, matches)"
            )
    return failures


async def run_eval_cases(target: EvalTarget, cases: Sequence[PromptEvalCase]) -> EvalReport:
    """Run every case's variables through `target` and check expectations.

    Raises:
        EvalError: on malformed expectations (never on a failing case —
            failures are results, reported in the EvalReport).
    """
    results: list[EvalCaseResult] = []
    for case in cases:
        output = await target(dict(case.variables))
        failures = _check_expected(output, case.expected, case.id)
        results.append(EvalCaseResult(case_id=case.id, passed=not failures, failures=failures))
    return EvalReport(results=results)

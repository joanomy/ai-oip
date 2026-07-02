"""Evals: the evaluation harness for prompt/agent golden cases (ADR-0006).

Runs the eval fixtures every prompt ships with (`evals/cases.yaml`)
against a completion callable and reports per-case pass/fail. "No
concrete agent ships without an eval suite" is enforced through this
package plus the prompt loader's refusal to load missing fixtures.

Dependency rule: depends on prompts, core. NEVER on repositories or
models (enforced by import-linter).
"""

from ai_oip.evals.runner import (
    EvalCaseResult,
    EvalReport,
    EvalTarget,
    run_eval_cases,
)
from ai_oip.evals.targets import prompt_completion_target

__all__ = [
    "EvalCaseResult",
    "EvalReport",
    "EvalTarget",
    "prompt_completion_target",
    "run_eval_cases",
]

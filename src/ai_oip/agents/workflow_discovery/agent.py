"""Workflow Discovery agent: stored problems in, underlying workflows out.

Second concrete agent, same recipe as problem extraction: one batched
completion over a numbered digest, 1-based `problem_indexes` in the
output so linkage survives batching.
"""

from collections.abc import Sequence

from ai_oip.agents.base import PromptedAgent
from ai_oip.schemas import ProblemDetail, WorkflowDiscoveryInput, WorkflowDiscoveryOutput


def _problems_digest(problems: Sequence[ProblemDetail]) -> str:
    """Render stored problems as the numbered digest the prompt expects."""
    blocks: list[str] = []
    for index, problem in enumerate(problems, start=1):
        lines = [f"[{index}] {problem.description}"]
        if problem.context:
            lines.append(f"    Context: {problem.context}")
        if problem.evidence:
            lines.append(f'    Evidence: "{problem.evidence}"')
        blocks.append("\n".join(lines))
    return "\n".join(blocks)


class WorkflowDiscoveryAgent(PromptedAgent[WorkflowDiscoveryInput, WorkflowDiscoveryOutput]):
    """Identifies the recurring business workflows behind stored problems."""

    name = "workflow_discovery"
    digest_variable = "problems_digest"
    output_schema = WorkflowDiscoveryOutput

    def digest(self, input_data: WorkflowDiscoveryInput) -> str:
        return _problems_digest(input_data.problems)

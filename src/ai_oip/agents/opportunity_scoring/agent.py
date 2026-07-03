"""Opportunity Scoring agent: workflows in, per-dimension judgments out.

Third concrete agent. It judges, only: the prompt explicitly forbids
totals/rankings — the deterministic weighted arithmetic lives in the
service, so tuning weights never touches a prompt.
"""

from collections.abc import Sequence

from ai_oip.agents.base import PromptedAgent
from ai_oip.schemas import (
    OpportunityScoringInput,
    OpportunityScoringOutput,
    WorkflowDetail,
)


def _workflows_digest(workflows: Sequence[WorkflowDetail]) -> str:
    """Render stored workflows as the numbered digest the prompt expects."""
    blocks: list[str] = []
    for index, workflow in enumerate(workflows, start=1):
        lines = [f"[{index}] {workflow.name} — {workflow.description}"]
        if workflow.steps:
            lines.append(f"    Steps: {'; '.join(workflow.steps)}")
        if workflow.actors:
            lines.append(f"    Actors: {', '.join(workflow.actors)}")
        lines.append(f"    Linked problems: {workflow.problems_linked}")
        blocks.append("\n".join(lines))
    return "\n".join(blocks)


class OpportunityScoringAgent(PromptedAgent[OpportunityScoringInput, OpportunityScoringOutput]):
    """Scores discovered workflows on the five opportunity dimensions."""

    name = "opportunity_scoring"
    digest_variable = "workflows_digest"
    output_schema = OpportunityScoringOutput

    def digest(self, input_data: OpportunityScoringInput) -> str:
        return _workflows_digest(input_data.workflows)

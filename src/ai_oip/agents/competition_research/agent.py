"""Competition Research agent: top opportunities in, landscape assessments out.

Model-knowledge only (v1, ADR-0013): the prompt constrains the agent
to competitors it is confident exist and forbids stale specifics
(pricing, funding). Web-search grounding is the planned v2, behind the
same interface.
"""

from collections.abc import Sequence

from ai_oip.agents.base import PromptedAgent
from ai_oip.schemas import (
    CompetitionResearchInput,
    CompetitionResearchOutput,
    ResearchTarget,
)


def _opportunities_digest(targets: Sequence[ResearchTarget]) -> str:
    """Render research targets as the numbered digest the prompt expects."""
    blocks: list[str] = []
    for index, target in enumerate(targets, start=1):
        workflow = target.workflow
        lines = [
            f"[{index}] {workflow.name} (opportunity score {target.total_score}/100) — "
            f"{workflow.description}"
        ]
        if workflow.steps:
            lines.append(f"    Steps: {'; '.join(workflow.steps)}")
        if workflow.actors:
            lines.append(f"    Actors: {', '.join(workflow.actors)}")
        blocks.append("\n".join(lines))
    return "\n".join(blocks)


class CompetitionResearchAgent(PromptedAgent[CompetitionResearchInput, CompetitionResearchOutput]):
    """Assesses the competitive landscape for top-ranked workflows."""

    name = "competition_research"
    digest_variable = "opportunities_digest"
    output_schema = CompetitionResearchOutput

    def digest(self, input_data: CompetitionResearchInput) -> str:
        return _opportunities_digest(input_data.targets)

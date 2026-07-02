"""Competition Research agent: top opportunities in, landscape assessments out.

Model-knowledge only (v1, ADR-0013): the prompt constrains the agent
to competitors it is confident exist and forbids stale specifics
(pricing, funding). Web-search grounding is the planned v2, behind the
same interface.
"""

from collections.abc import Sequence

from ai_oip.agents.base import BaseAgent, parse_json_output
from ai_oip.prompts import PromptTemplate
from ai_oip.providers import CompletionRequest, LLMProvider
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


class CompetitionResearchAgent(BaseAgent[CompetitionResearchInput, CompetitionResearchOutput]):
    """Assesses the competitive landscape for top-ranked workflows."""

    name = "competition_research"

    def __init__(self, *, provider: LLMProvider, prompt: PromptTemplate) -> None:
        self._provider = provider
        self._prompt = prompt

    async def run(self, input_data: CompetitionResearchInput) -> CompetitionResearchOutput:
        rendered = self._prompt.render(
            opportunities_digest=_opportunities_digest(input_data.targets)
        )
        response = await self._provider.complete(
            CompletionRequest(prompt=rendered, system=self._prompt.metadata.role)
        )
        return parse_json_output(response.text, CompetitionResearchOutput, agent_name=self.name)

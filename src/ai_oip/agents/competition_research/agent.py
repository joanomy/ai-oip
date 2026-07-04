"""Competition Research agent: top opportunities in, landscape assessments out.

v2 (R1, ADR-0018) grounds the assessment in live web search via the
provider seam — the agent passes `WebSearchOptions` through and the
prompt requires claims to be supported by results. The honesty
constraints from v1 (ADR-0013) still hold: never invent a competitor,
and empty-competitors/low-saturation remains a valid answer when the
search comes back thin. Constructed without options, the agent runs
ungrounded exactly as v1 did.
"""

from collections.abc import Sequence

from ai_oip.agents.base import PromptedAgent
from ai_oip.prompts import PromptTemplate
from ai_oip.providers import CompletionRequest, LLMProvider, WebSearchOptions
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

    def __init__(
        self,
        *,
        provider: LLMProvider,
        prompt: PromptTemplate,
        web_search: WebSearchOptions | None = None,
    ) -> None:
        super().__init__(provider=provider, prompt=prompt)
        self._web_search = web_search

    @property
    def grounded(self) -> bool:
        """True if this agent instance grounds assessments in web search."""
        return self._web_search is not None

    def build_request(self, rendered: str) -> CompletionRequest:
        return CompletionRequest(
            prompt=rendered,
            system=self._prompt.metadata.role,
            web_search=self._web_search,
        )

    def digest(self, input_data: CompetitionResearchInput) -> str:
        return _opportunities_digest(input_data.targets)

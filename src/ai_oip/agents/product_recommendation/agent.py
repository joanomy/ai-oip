"""Product Recommendation agent: researched opportunities in, build/watch/pass
plans out.

Each target already carries a competitive assessment (M11) — the digest
surfaces saturation, gap, and known competitors alongside the workflow
itself, so the recommendation is grounded in both the opportunity and
the landscape it would launch into.
"""

from collections.abc import Sequence

from ai_oip.agents.base import PromptedAgent
from ai_oip.schemas import (
    ProductRecommendationInput,
    ProductRecommendationOutput,
    RecommendationTarget,
)


def _targets_digest(targets: Sequence[RecommendationTarget]) -> str:
    """Render recommendation targets as the numbered digest the prompt expects."""
    blocks: list[str] = []
    for index, target in enumerate(targets, start=1):
        workflow = target.workflow
        competition = target.competition
        lines = [
            f"[{index}] {workflow.name} (opportunity score {target.total_score}/100) — "
            f"{workflow.description}"
        ]
        if workflow.steps:
            lines.append(f"    Steps: {'; '.join(workflow.steps)}")
        if workflow.actors:
            lines.append(f"    Actors: {', '.join(workflow.actors)}")
        competitor_names = ", ".join(c.name for c in competition.competitors) or "none known"
        lines.append(
            f"    Competitive landscape: saturation {competition.saturation}; "
            f"competitors: {competitor_names}"
        )
        if competition.market_gap:
            lines.append(f"    Gap: {competition.market_gap}")
        blocks.append("\n".join(lines))
    return "\n".join(blocks)


class ProductRecommendationAgent(
    PromptedAgent[ProductRecommendationInput, ProductRecommendationOutput]
):
    """Recommends build/watch/pass and an MVP concept per researched opportunity."""

    name = "product_recommendation"
    digest_variable = "targets_digest"
    output_schema = ProductRecommendationOutput

    def digest(self, input_data: ProductRecommendationInput) -> str:
        return _targets_digest(input_data.targets)

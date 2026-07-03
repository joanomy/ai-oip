"""Product-recommendation composition: one pass over researched opportunities.

Invoked via the unified CLI (`ai-oip recommend`).
"""

from sqlalchemy.ext.asyncio import AsyncEngine

from ai_oip.agents.product_recommendation import ProductRecommendationAgent
from ai_oip.config import Settings
from ai_oip.prompts import PromptLoader
from ai_oip.providers import LLMProvider
from ai_oip.repositories import (
    CompetitionRepository,
    OpportunityRepository,
    ProductRecommendationRepository,
    WorkflowRepository,
)
from ai_oip.runtime.composition import stage_context
from ai_oip.schemas import RecommendationReport
from ai_oip.services import ProductRecommendationService, render_recommendation_report

PROMPT_NAME = "product_recommendation"


async def run_product_recommendation(
    *,
    limit: int = 5,
    settings: Settings | None = None,
    engine: AsyncEngine | None = None,
    provider: LLMProvider | None = None,
    prompt_loader: PromptLoader | None = None,
) -> tuple[RecommendationReport, str]:
    """Compose and execute one product-recommendation run."""
    async with stage_context(
        settings=settings, engine=engine, provider=provider, prompt_loader=prompt_loader
    ) as ctx:
        agent = ProductRecommendationAgent(
            provider=ctx.provider, prompt=ctx.prompt_loader.load(PROMPT_NAME)
        )
        service = ProductRecommendationService(
            agent=agent,
            opportunity_repository=OpportunityRepository(ctx.session),
            workflow_repository=WorkflowRepository(ctx.session),
            competition_repository=CompetitionRepository(ctx.session),
            recommendation_repository=ProductRecommendationRepository(ctx.session),
        )
        report = await service.recommend(limit=limit)

    return report, render_recommendation_report(report)

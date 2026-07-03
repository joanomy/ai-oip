"""Opportunity-scoring composition: one pass over stored workflows.

No standalone script — invoked via the unified CLI (`ai-oip score`,
see runtime/cli.py, ADR-0011's consolidation note come due).
"""

from sqlalchemy.ext.asyncio import AsyncEngine

from ai_oip.agents.opportunity_scoring import OpportunityScoringAgent
from ai_oip.config import Settings
from ai_oip.prompts import PromptLoader
from ai_oip.providers import LLMProvider
from ai_oip.repositories import OpportunityRepository, WorkflowRepository
from ai_oip.runtime.composition import stage_context
from ai_oip.schemas import OpportunityReport
from ai_oip.services import OpportunityScoringService, render_opportunity_report

PROMPT_NAME = "score_opportunities"


async def run_opportunity_scoring(
    *,
    limit: int = 20,
    settings: Settings | None = None,
    engine: AsyncEngine | None = None,
    provider: LLMProvider | None = None,
    prompt_loader: PromptLoader | None = None,
    weights: dict[str, float] | None = None,
) -> tuple[OpportunityReport, str]:
    """Compose and execute one opportunity-scoring run."""
    async with stage_context(
        settings=settings, engine=engine, provider=provider, prompt_loader=prompt_loader
    ) as ctx:
        agent = OpportunityScoringAgent(
            provider=ctx.provider, prompt=ctx.prompt_loader.load(PROMPT_NAME)
        )
        service = OpportunityScoringService(
            agent=agent,
            workflow_repository=WorkflowRepository(ctx.session),
            opportunity_repository=OpportunityRepository(ctx.session),
            weights=weights,
        )
        report = await service.score(limit=limit)

    return report, render_opportunity_report(report)

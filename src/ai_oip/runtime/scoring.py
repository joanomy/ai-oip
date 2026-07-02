"""Opportunity-scoring composition: one pass over stored workflows.

No standalone script — invoked via the unified CLI (`ai-oip score`,
see runtime/cli.py, ADR-0011's consolidation note come due).
"""

from sqlalchemy.ext.asyncio import AsyncEngine

from ai_oip.agents.opportunity_scoring import OpportunityScoringAgent
from ai_oip.config import Settings, get_settings
from ai_oip.models import create_engine_from_settings, create_session_factory, session_scope
from ai_oip.prompts import PromptLoader
from ai_oip.providers import LLMProvider, anthropic_provider_from_settings
from ai_oip.repositories import OpportunityRepository, WorkflowRepository
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
    settings = settings if settings is not None else get_settings()
    owns_engine = engine is None
    engine = engine if engine is not None else create_engine_from_settings(settings)
    provider = provider if provider is not None else anthropic_provider_from_settings(settings)
    loader = prompt_loader if prompt_loader is not None else PromptLoader()

    prompt = loader.load(PROMPT_NAME)
    agent = OpportunityScoringAgent(provider=provider, prompt=prompt)
    session_factory = create_session_factory(engine)

    try:
        async with session_scope(session_factory) as session:
            service = OpportunityScoringService(
                agent=agent,
                workflow_repository=WorkflowRepository(session),
                opportunity_repository=OpportunityRepository(session),
                weights=weights,
            )
            report = await service.score(limit=limit)
    finally:
        if owns_engine:
            await engine.dispose()

    return report, render_opportunity_report(report)

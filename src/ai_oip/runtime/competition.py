"""Competition-research composition: one pass over top-scored workflows.

Invoked via the unified CLI (`ai-oip research`).
"""

from sqlalchemy.ext.asyncio import AsyncEngine

from ai_oip.agents.competition_research import CompetitionResearchAgent
from ai_oip.config import Settings, get_settings
from ai_oip.models import create_engine_from_settings, create_session_factory, session_scope
from ai_oip.prompts import PromptLoader
from ai_oip.providers import LLMProvider, anthropic_provider_from_settings
from ai_oip.repositories import (
    CompetitionRepository,
    OpportunityRepository,
    WorkflowRepository,
)
from ai_oip.schemas import CompetitionReport
from ai_oip.services import CompetitionResearchService, render_competition_report

PROMPT_NAME = "research_competition"


async def run_competition_research(
    *,
    limit: int = 5,
    settings: Settings | None = None,
    engine: AsyncEngine | None = None,
    provider: LLMProvider | None = None,
    prompt_loader: PromptLoader | None = None,
) -> tuple[CompetitionReport, str]:
    """Compose and execute one competition-research run."""
    settings = settings if settings is not None else get_settings()
    owns_engine = engine is None
    engine = engine if engine is not None else create_engine_from_settings(settings)
    provider = provider if provider is not None else anthropic_provider_from_settings(settings)
    loader = prompt_loader if prompt_loader is not None else PromptLoader()

    prompt = loader.load(PROMPT_NAME)
    agent = CompetitionResearchAgent(provider=provider, prompt=prompt)
    session_factory = create_session_factory(engine)

    try:
        async with session_scope(session_factory) as session:
            service = CompetitionResearchService(
                agent=agent,
                opportunity_repository=OpportunityRepository(session),
                workflow_repository=WorkflowRepository(session),
                competition_repository=CompetitionRepository(session),
            )
            report = await service.research(limit=limit)
    finally:
        if owns_engine:
            await engine.dispose()

    return report, render_competition_report(report)

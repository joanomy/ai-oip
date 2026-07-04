"""Competition-research composition: one pass over top-scored workflows.

Invoked via the unified CLI (`ai-oip research`).

Grounded by default (R1, ADR-0018): production runs assess competitors
against live web search rather than model knowledge alone. `grounded`
stays a parameter, not a deletion of the v1 path, so an ungrounded run
remains one call away if search cost or availability ever demands it.
"""

from sqlalchemy.ext.asyncio import AsyncEngine

from ai_oip.agents.competition_research import CompetitionResearchAgent
from ai_oip.config import Settings
from ai_oip.prompts import PromptLoader
from ai_oip.providers import LLMProvider, WebSearchOptions
from ai_oip.repositories import (
    CompetitionRepository,
    OpportunityRepository,
    WorkflowRepository,
)
from ai_oip.runtime.composition import stage_context
from ai_oip.schemas import CompetitionReport
from ai_oip.services import CompetitionResearchService, render_competition_report

PROMPT_NAME = "research_competition"


async def run_competition_research(
    *,
    limit: int = 5,
    grounded: bool = True,
    web_search_max_uses: int | None = None,
    settings: Settings | None = None,
    engine: AsyncEngine | None = None,
    provider: LLMProvider | None = None,
    prompt_loader: PromptLoader | None = None,
) -> tuple[CompetitionReport, str]:
    """Compose and execute one competition-research run.

    `web_search_max_uses` of None defers to
    `Settings.competition_research_web_search_max_uses`; it is ignored
    when `grounded=False`.
    """
    async with stage_context(
        settings=settings, engine=engine, provider=provider, prompt_loader=prompt_loader
    ) as ctx:
        web_search = (
            WebSearchOptions(
                max_uses=web_search_max_uses
                if web_search_max_uses is not None
                else ctx.settings.competition_research_web_search_max_uses
            )
            if grounded
            else None
        )
        agent = CompetitionResearchAgent(
            provider=ctx.provider,
            prompt=ctx.prompt_loader.load(PROMPT_NAME),
            web_search=web_search,
        )
        service = CompetitionResearchService(
            agent=agent,
            opportunity_repository=OpportunityRepository(ctx.session),
            workflow_repository=WorkflowRepository(ctx.session),
            competition_repository=CompetitionRepository(ctx.session),
        )
        report = await service.research(limit=limit)

    return report, render_competition_report(report)

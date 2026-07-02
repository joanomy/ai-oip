"""Workflow-discovery entrypoint: one human-triggered pass over stored problems.

Reads recent problems from the database, discovers the workflows
behind them, persists them, and renders a markdown report. Same
composition pattern (and the same override seams) as the skeleton.
"""

import argparse
import asyncio
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncEngine

from ai_oip.agents.workflow_discovery import WorkflowDiscoveryAgent
from ai_oip.config import Settings, get_settings
from ai_oip.logging import configure_logging, get_logger
from ai_oip.models import create_engine_from_settings, create_session_factory, session_scope
from ai_oip.prompts import PromptLoader
from ai_oip.providers import LLMProvider, anthropic_provider_from_settings
from ai_oip.repositories import ProblemRepository, WorkflowRepository
from ai_oip.schemas import WorkflowReport
from ai_oip.services import WorkflowDiscoveryService, render_workflow_report

PROMPT_NAME = "discover_workflows"


async def run_workflow_discovery(
    *,
    limit: int = 50,
    settings: Settings | None = None,
    engine: AsyncEngine | None = None,
    provider: LLMProvider | None = None,
    prompt_loader: PromptLoader | None = None,
) -> tuple[WorkflowReport, str]:
    """Compose and execute one workflow-discovery run."""
    settings = settings if settings is not None else get_settings()
    owns_engine = engine is None
    engine = engine if engine is not None else create_engine_from_settings(settings)
    provider = provider if provider is not None else anthropic_provider_from_settings(settings)
    loader = prompt_loader if prompt_loader is not None else PromptLoader()

    prompt = loader.load(PROMPT_NAME)
    agent = WorkflowDiscoveryAgent(provider=provider, prompt=prompt)
    session_factory = create_session_factory(engine)

    try:
        async with session_scope(session_factory) as session:
            service = WorkflowDiscoveryService(
                agent=agent,
                problem_repository=ProblemRepository(session),
                workflow_repository=WorkflowRepository(session),
            )
            report = await service.discover(limit=limit)
    finally:
        if owns_engine:
            await engine.dispose()

    return report, render_workflow_report(report)


def main() -> None:  # pragma: no cover — thin argv shell over run_workflow_discovery
    parser = argparse.ArgumentParser(
        description="Discover the business workflows behind stored problems."
    )
    parser.add_argument("--limit", type=int, default=50, help="Max stored problems to analyze")
    parser.add_argument("--output", type=Path, default=None, help="Write markdown report here")
    args = parser.parse_args()

    settings = get_settings()
    configure_logging(settings)
    logger = get_logger("ai_oip.runtime")

    report, markdown = asyncio.run(run_workflow_discovery(limit=args.limit))
    logger.info(
        "workflow_discovery_completed",
        problems_analyzed=report.problems_analyzed,
        workflows_discovered=len(report.workflows),
    )
    if args.output is not None:
        args.output.write_text(markdown, encoding="utf-8")
    else:
        print(markdown)  # noqa: T201 — CLI output is the point


if __name__ == "__main__":  # pragma: no cover
    main()

"""Walking-skeleton entrypoint: one human-triggered end-to-end run.

Collect (Hacker News) -> extract problems (agent) -> persist
(Postgres) -> markdown report. Every dependency is overridable for
tests; production wiring comes entirely from Settings.

Prerequisite for a real run: a migrated database (`alembic upgrade
head`) and ANTHROPIC_API_KEY set.
"""

import argparse
import asyncio
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncEngine

from ai_oip.agents.problem_extraction import ProblemExtractionAgent
from ai_oip.collectors import BaseCollector, HackerNewsCollector
from ai_oip.config import Settings, get_settings
from ai_oip.logging import configure_logging, get_logger
from ai_oip.prompts import PromptLoader
from ai_oip.providers import LLMProvider
from ai_oip.repositories import ProblemRepository
from ai_oip.runtime.composition import stage_context
from ai_oip.schemas import SkeletonReport
from ai_oip.services import ProblemDiscoveryService, render_markdown_report

PROMPT_NAME = "extract_problems"


async def run_skeleton(
    query: str,
    *,
    limit: int = 20,
    settings: Settings | None = None,
    engine: AsyncEngine | None = None,
    provider: LLMProvider | None = None,
    collector: BaseCollector | None = None,
    prompt_loader: PromptLoader | None = None,
) -> tuple[SkeletonReport, str]:
    """Compose the pipeline and execute one discovery run.

    Returns the typed report and its markdown rendering. Keyword
    overrides exist for tests and future callers; None means "wire the
    production default from Settings".
    """
    collector = collector if collector is not None else HackerNewsCollector()
    async with stage_context(
        settings=settings, engine=engine, provider=provider, prompt_loader=prompt_loader
    ) as ctx:
        agent = ProblemExtractionAgent(
            provider=ctx.provider, prompt=ctx.prompt_loader.load(PROMPT_NAME)
        )
        service = ProblemDiscoveryService(
            collector=collector,
            agent=agent,
            repository=ProblemRepository(ctx.session),
        )
        report = await service.discover(query, limit=limit)

    return report, render_markdown_report(report)


def main() -> None:  # pragma: no cover — thin argv shell over run_skeleton
    parser = argparse.ArgumentParser(
        description="Run one end-to-end problem-discovery pass (walking skeleton)."
    )
    parser.add_argument("query", help="Search query for the collector (e.g. 'automation pain')")
    parser.add_argument("--limit", type=int, default=20, help="Max items to collect")
    parser.add_argument("--output", type=Path, default=None, help="Write markdown report here")
    args = parser.parse_args()

    settings = get_settings()
    configure_logging(settings)
    logger = get_logger("ai_oip.runtime")

    report, markdown = asyncio.run(run_skeleton(args.query, limit=args.limit))
    logger.info(
        "skeleton_run_completed",
        query=report.query,
        items_collected=report.items_collected,
        problems_found=len(report.findings),
    )
    if args.output is not None:
        args.output.write_text(markdown, encoding="utf-8")
    else:
        print(markdown)  # noqa: T201 — CLI output is the point


if __name__ == "__main__":  # pragma: no cover
    main()

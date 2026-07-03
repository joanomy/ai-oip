"""Unified CLI: `ai-oip <stage>` — the consolidation ADR-0011 called for.

Subcommands map 1:1 to pipeline stages; each delegates to the stage's
composition function. The per-stage legacy scripts (ai-oip-skeleton,
ai-oip-workflows) remain as aliases.
"""

import argparse
import asyncio
from pathlib import Path

from ai_oip.config import get_settings
from ai_oip.logging import configure_logging, get_logger
from ai_oip.runtime.competition import run_competition_research
from ai_oip.runtime.product_recommendation import run_product_recommendation
from ai_oip.runtime.scoring import run_opportunity_scoring
from ai_oip.runtime.skeleton import run_skeleton
from ai_oip.runtime.workflows import run_workflow_discovery


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ai-oip", description="AI Opportunity Intelligence Platform pipeline stages."
    )
    subcommands = parser.add_subparsers(dest="command", required=True)

    discover = subcommands.add_parser(
        "discover", help="Collect raw signal and extract problems (stage 1)"
    )
    discover.add_argument("query", help="Search query for the collector")
    discover.add_argument("--limit", type=int, default=20)
    discover.add_argument("--output", type=Path, default=None)

    workflows = subcommands.add_parser(
        "workflows", help="Discover workflows behind stored problems (stage 2)"
    )
    workflows.add_argument("--limit", type=int, default=50)
    workflows.add_argument("--output", type=Path, default=None)

    score = subcommands.add_parser(
        "score", help="Score stored workflows as opportunities (stage 3)"
    )
    score.add_argument("--limit", type=int, default=20)
    score.add_argument("--output", type=Path, default=None)

    research = subcommands.add_parser(
        "research", help="Research competition for top opportunities (stage 4)"
    )
    research.add_argument("--limit", type=int, default=5)
    research.add_argument("--output", type=Path, default=None)

    recommend = subcommands.add_parser(
        "recommend", help="Recommend build/watch/pass for researched opportunities (stage 5)"
    )
    recommend.add_argument("--limit", type=int, default=5)
    recommend.add_argument("--output", type=Path, default=None)

    return parser


def main() -> None:  # pragma: no cover — thin argv shell over the run_* functions
    args = build_parser().parse_args()
    settings = get_settings()
    configure_logging(settings)
    logger = get_logger("ai_oip.runtime")

    markdown: str
    if args.command == "discover":
        _, markdown = asyncio.run(run_skeleton(args.query, limit=args.limit))
    elif args.command == "workflows":
        _, markdown = asyncio.run(run_workflow_discovery(limit=args.limit))
    elif args.command == "score":
        _, markdown = asyncio.run(run_opportunity_scoring(limit=args.limit))
    elif args.command == "research":
        _, markdown = asyncio.run(run_competition_research(limit=args.limit))
    else:
        _, markdown = asyncio.run(run_product_recommendation(limit=args.limit))

    logger.info("pipeline_stage_completed", command=args.command)
    if args.output is not None:
        args.output.write_text(markdown, encoding="utf-8")
    else:
        print(markdown)  # noqa: T201 — CLI output is the point

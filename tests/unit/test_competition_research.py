"""Tests for M11: competition research — two-store read with dedupe,
honesty-constrained agent, persistence, runtime, eval fixtures."""

import json

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from ai_oip.agents.competition_research import CompetitionResearchAgent
from ai_oip.config import Settings
from ai_oip.core.exceptions import AgentExecutionError
from ai_oip.evals import prompt_completion_target, run_eval_cases
from ai_oip.models import create_session_factory
from ai_oip.prompts import PromptLoader
from ai_oip.providers import WebSearchOptions
from ai_oip.repositories import (
    CompetitionRepository,
    OpportunityRepository,
    WorkflowRepository,
)
from ai_oip.runtime.competition import run_competition_research
from ai_oip.schemas import (
    CompetitionResearchInput,
    DimensionScore,
    DiscoveredWorkflow,
    ResearchTarget,
    WorkflowScore,
)
from ai_oip.services import CompetitionResearchService, render_competition_report
from tests.fixtures.fakes import FakeProvider

ASSESSMENT_OUTPUT = json.dumps(
    {
        "assessments": [
            {
                "workflow_index": 1,
                "competitors": [
                    {
                        "name": "Acme OCR",
                        "offering": "Invoice data extraction",
                        "positioning": "Mid-market accounting teams",
                    }
                ],
                "market_gap": "No SMB-priced option with reconciliation built in.",
                "saturation": "medium",
            },
            {"workflow_index": 99, "competitors": [], "market_gap": None, "saturation": "low"},
        ]
    }
)


def _uniform_score(index: int, value: int) -> WorkflowScore:
    dim = DimensionScore(score=value, rationale="r")
    return WorkflowScore(
        workflow_index=index,
        pain_intensity=dim,
        automation_feasibility=dim,
        frequency=dim,
        market_breadth=dim,
        willingness_to_pay=dim,
    )


async def _seed_scored_workflows(session: AsyncSession, scores: list[int]) -> None:
    """Seed one workflow + one opportunity score per entry in `scores`."""
    workflow_repo = WorkflowRepository(session)
    opportunity_repo = OpportunityRepository(session)
    for index, value in enumerate(scores, start=1):
        await workflow_repo.add_discovered(
            DiscoveredWorkflow(
                name=f"Workflow {index}",
                description=f"Description {index}",
                steps=["step"],
                actors=["Analyst"],
            ),
            problem_ids=[],
        )
        details = await workflow_repo.list_details(limit=1)
        await opportunity_repo.add_score(
            workflow=details[0],
            score=_uniform_score(1, value),
            total_score=float(value * 10),
        )


def _service(
    db_session: AsyncSession,
    provider: FakeProvider,
    *,
    web_search: WebSearchOptions | None = None,
) -> CompetitionResearchService:
    return CompetitionResearchService(
        agent=CompetitionResearchAgent(
            provider=provider,
            prompt=PromptLoader().load("research_competition"),
            web_search=web_search,
        ),
        opportunity_repository=OpportunityRepository(db_session),
        workflow_repository=WorkflowRepository(db_session),
        competition_repository=CompetitionRepository(db_session),
    )


class TestPromptAndAgent:
    async def test_packaged_prompt_contract(self) -> None:
        prompt = PromptLoader().load("research_competition")

        assert prompt.metadata.name == "research_competition"
        # v2 (R1, ADR-0018) is the latest/default version.
        assert prompt.metadata.version == 2
        assert prompt.variables == {"opportunities_digest"}
        # The honesty constraints are load-bearing — pin them.
        assert "NEVER invent" in "\n".join(prompt.metadata.validation_rules)

    async def test_v2_prompt_requires_grounding(self) -> None:
        # Pinned per ADR-0018: v2's honesty constraint is search-first,
        # not just never-invent — a prompt edit that silently drops the
        # grounding instruction should fail this test.
        prompt = PromptLoader().load("research_competition", version=2)

        assert "search" in prompt.metadata.role.lower()
        assert "search the web" in prompt.metadata.objective.lower()

    async def test_v1_prompt_still_loadable_as_history(self) -> None:
        # ADR-0007: prompt versions are retained, diffable history —
        # v1 (model-knowledge-only, ADR-0013) stays loadable by number
        # even though v2 is now the default.
        prompt = PromptLoader().load("research_competition", version=1)

        assert prompt.metadata.version == 1
        assert "search" not in prompt.metadata.role.lower()

    async def test_agent_renders_digest_and_parses(self, db_session) -> None:
        await _seed_scored_workflows(db_session, scores=[8])
        details = await WorkflowRepository(db_session).list_details()
        provider = FakeProvider(ASSESSMENT_OUTPUT)
        agent = CompetitionResearchAgent(
            provider=provider, prompt=PromptLoader().load("research_competition")
        )

        output = await agent.run(
            CompetitionResearchInput(
                targets=[ResearchTarget(workflow=details[0], total_score=80.0)]
            )
        )

        assert output.assessments[0].competitors[0].name == "Acme OCR"
        request = provider.requests[0]
        assert "(opportunity score 80.0/100)" in request.prompt

    async def test_invalid_saturation_fails_validation(self) -> None:
        bad = ASSESSMENT_OUTPUT.replace('"medium"', '"extreme"')
        agent = CompetitionResearchAgent(
            provider=FakeProvider(bad), prompt=PromptLoader().load("research_competition")
        )

        with pytest.raises(AgentExecutionError, match=r"\[competition_research\]"):
            await agent.run(CompetitionResearchInput(targets=[]))

    async def test_eval_fixtures_run_through_the_harness(self) -> None:
        prompt = PromptLoader().load("research_competition")
        cases = PromptLoader().load_eval_cases("research_competition")
        target = prompt_completion_target(prompt, FakeProvider('{"assessments": []}'))

        report = await run_eval_cases(target, cases)

        assert report.passed is True

    async def test_agent_ungrounded_by_default(self) -> None:
        provider = FakeProvider(ASSESSMENT_OUTPUT)
        agent = CompetitionResearchAgent(
            provider=provider, prompt=PromptLoader().load("research_competition")
        )

        assert agent.grounded is False
        await agent.run(CompetitionResearchInput(targets=[]))
        assert provider.requests[0].web_search is None

    async def test_agent_grounded_attaches_web_search_to_the_request(self) -> None:
        provider = FakeProvider(ASSESSMENT_OUTPUT, sources=("https://a.example",))
        agent = CompetitionResearchAgent(
            provider=provider,
            prompt=PromptLoader().load("research_competition"),
            web_search=WebSearchOptions(max_uses=3),
        )

        assert agent.grounded is True
        output, response = await agent.run_detailed(CompetitionResearchInput(targets=[]))

        assert provider.requests[0].web_search == WebSearchOptions(max_uses=3)
        assert response.sources == ("https://a.example",)
        assert output.assessments  # parsed same as the ungrounded path


class TestService:
    async def test_research_persists_and_drops_invalid_index(self, db_session) -> None:
        await _seed_scored_workflows(db_session, scores=[9])
        service = _service(db_session, FakeProvider(ASSESSMENT_OUTPUT))

        report = await service.research(limit=5)

        assert report.targets_analyzed == 1
        assert len(report.assessments) == 1  # index 99 dropped
        assessment = report.assessments[0]
        assert assessment.saturation == "medium"
        assert assessment.competitors[0].offering == "Invoice data extraction"

        rows = await CompetitionRepository(db_session).list_all()
        assert len(rows) == 1
        assert rows[0].saturation == "medium"
        assert rows[0].competitors[0]["name"] == "Acme OCR"

    async def test_rescored_workflow_is_researched_once_at_best_score(self, db_session) -> None:
        # One workflow scored twice (re-scoring run): dedupe keeps best.
        workflow_repo = WorkflowRepository(db_session)
        opportunity_repo = OpportunityRepository(db_session)
        await workflow_repo.add_discovered(
            DiscoveredWorkflow(name="W", description="D", steps=[], actors=[]),
            problem_ids=[],
        )
        detail = (await workflow_repo.list_details())[0]
        await opportunity_repo.add_score(
            workflow=detail, score=_uniform_score(1, 5), total_score=50.0
        )
        await opportunity_repo.add_score(
            workflow=detail, score=_uniform_score(1, 8), total_score=80.0
        )
        provider = FakeProvider(ASSESSMENT_OUTPUT)
        service = _service(db_session, provider)

        report = await service.research(limit=5)

        assert report.targets_analyzed == 1
        assert report.assessments[0].total_score == 80.0
        assert "(opportunity score 80.0/100)" in provider.requests[0].prompt

    async def test_no_scores_skips_the_agent(self, db_session) -> None:
        provider = FakeProvider("{}")
        service = _service(db_session, provider)

        report = await service.research()

        assert report.targets_analyzed == 0
        assert provider.requests == []

    async def test_ungrounded_run_persists_no_sources(self, db_session) -> None:
        await _seed_scored_workflows(db_session, scores=[9])
        service = _service(db_session, FakeProvider(ASSESSMENT_OUTPUT))

        report = await service.research(limit=5)

        assert report.grounded is False
        assert report.assessments[0].sources == ()
        rows = await CompetitionRepository(db_session).list_all()
        assert rows[0].sources is None

    async def test_grounded_run_persists_batch_level_sources(self, db_session) -> None:
        await _seed_scored_workflows(db_session, scores=[9])
        sources = ("https://vendor-a.example", "https://vendor-b.example")
        service = _service(
            db_session,
            FakeProvider(ASSESSMENT_OUTPUT, sources=sources),
            web_search=WebSearchOptions(max_uses=4),
        )

        report = await service.research(limit=5)

        assert report.grounded is True
        assert report.assessments[0].sources == sources
        rows = await CompetitionRepository(db_session).list_all()
        assert rows[0].sources == list(sources)


class TestRuntimeAndReport:
    async def test_end_to_end_on_sqlite_is_grounded_by_default(
        self, db_engine: AsyncEngine
    ) -> None:
        factory = create_session_factory(db_engine)
        async with factory() as session:
            await _seed_scored_workflows(session, scores=[7])
            await session.commit()

        provider = FakeProvider(ASSESSMENT_OUTPUT, sources=("https://vendor.example",))
        report, markdown = await run_competition_research(
            limit=5,
            settings=Settings(_env_file=None),
            engine=db_engine,
            provider=provider,
        )

        assert report.targets_analyzed == 1
        assert report.grounded is True
        assert "# Competition Research Report" in markdown
        assert "saturation: medium" in markdown
        assert "**Acme OCR**: Invoice data extraction — Mid-market accounting teams" in markdown
        assert "**Gap:** No SMB-priced option" in markdown
        assert "grounded in live web search" in markdown  # R1 honesty banner
        assert "1 source consulted" in markdown
        # Defaults to Settings.competition_research_web_search_max_uses.
        assert provider.requests[0].web_search.max_uses == 5

    async def test_end_to_end_ungrounded_keeps_the_knowledge_lag_banner(
        self, db_engine: AsyncEngine
    ) -> None:
        factory = create_session_factory(db_engine)
        async with factory() as session:
            await _seed_scored_workflows(session, scores=[7])
            await session.commit()

        report, markdown = await run_competition_research(
            limit=5,
            grounded=False,
            settings=Settings(_env_file=None),
            engine=db_engine,
            provider=FakeProvider(ASSESSMENT_OUTPUT),
        )

        assert report.grounded is False
        assert "may lag the" in markdown  # v1 honesty banner, still available on request

    async def test_explicit_max_uses_overrides_settings_default(
        self, db_engine: AsyncEngine
    ) -> None:
        factory = create_session_factory(db_engine)
        async with factory() as session:
            await _seed_scored_workflows(session, scores=[7])
            await session.commit()

        provider = FakeProvider(ASSESSMENT_OUTPUT)
        await run_competition_research(
            limit=5,
            web_search_max_uses=2,
            settings=Settings(_env_file=None),
            engine=db_engine,
            provider=provider,
        )

        assert provider.requests[0].web_search.max_uses == 2

    async def test_report_renders_empty_state(self) -> None:
        from ai_oip.schemas import CompetitionReport

        markdown = render_competition_report(CompetitionReport(targets_analyzed=0, assessments=[]))

        assert "_No scored opportunities were available to research._" in markdown

    def test_cli_has_research_subcommand(self) -> None:
        from ai_oip.runtime.cli import build_parser

        args = build_parser().parse_args(["research", "--limit", "3"])

        assert (args.command, args.limit) == ("research", 3)

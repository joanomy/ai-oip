"""Tests for M10: opportunity scoring — deterministic weighting, agent,
repositories, service ranking, runtime entrypoint, eval fixtures."""

import json

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from ai_oip.agents.opportunity_scoring import OpportunityScoringAgent
from ai_oip.config import Settings
from ai_oip.core.exceptions import AgentExecutionError
from ai_oip.evals import prompt_completion_target, run_eval_cases
from ai_oip.models import create_session_factory
from ai_oip.prompts import PromptLoader
from ai_oip.repositories import OpportunityRepository, WorkflowRepository
from ai_oip.runtime.scoring import run_opportunity_scoring
from ai_oip.schemas import (
    DimensionScore,
    DiscoveredWorkflow,
    OpportunityScoringInput,
    WorkflowScore,
)
from ai_oip.services import (
    DEFAULT_WEIGHTS,
    OpportunityScoringService,
    render_opportunity_report,
    weighted_total,
)
from tests.fixtures.fakes import FakeProvider


def _dimension(score: int) -> dict:
    return {"score": score, "rationale": "grounded reason"}


def _score_payload(*entries: tuple[int, dict[str, int]]) -> str:
    scores = []
    for workflow_index, dims in entries:
        scores.append(
            {
                "workflow_index": workflow_index,
                "pain_intensity": _dimension(dims.get("pain", 5)),
                "automation_feasibility": _dimension(dims.get("auto", 5)),
                "frequency": _dimension(dims.get("freq", 5)),
                "market_breadth": _dimension(dims.get("market", 5)),
                "willingness_to_pay": _dimension(dims.get("pay", 5)),
            }
        )
    return json.dumps({"scores": scores})


async def _seed_workflows(session: AsyncSession, count: int = 2) -> WorkflowRepository:
    repo = WorkflowRepository(session)
    for index in range(1, count + 1):
        await repo.add_discovered(
            DiscoveredWorkflow(
                name=f"Workflow {index}",
                description=f"Description {index}",
                steps=["step one", "step two"],
                actors=["Analyst"],
            ),
            problem_ids=[],
        )
    return repo


def _make_score(value: int) -> WorkflowScore:
    dim = DimensionScore(score=value, rationale="r")
    return WorkflowScore(
        workflow_index=1,
        pain_intensity=dim,
        automation_feasibility=dim,
        frequency=dim,
        market_breadth=dim,
        willingness_to_pay=dim,
    )


class TestWeighting:
    def test_uniform_scores_scale_linearly(self) -> None:
        assert weighted_total(_make_score(10), DEFAULT_WEIGHTS) == 100.0
        assert weighted_total(_make_score(1), DEFAULT_WEIGHTS) == 10.0
        assert weighted_total(_make_score(5), DEFAULT_WEIGHTS) == 50.0

    def test_weights_shift_the_total(self) -> None:
        dim_high = DimensionScore(score=10, rationale="r")
        dim_low = DimensionScore(score=1, rationale="r")
        score = WorkflowScore(
            workflow_index=1,
            pain_intensity=dim_high,  # weight 0.25
            automation_feasibility=dim_low,
            frequency=dim_low,
            market_breadth=dim_low,
            willingness_to_pay=dim_low,
        )

        # 10*0.25 + 1*0.75 = 3.25 -> 32.5
        assert weighted_total(score, DEFAULT_WEIGHTS) == 32.5

    def test_default_weights_sum_to_one(self) -> None:
        assert round(sum(DEFAULT_WEIGHTS.values()), 6) == 1.0


class TestPromptAndAgent:
    async def test_packaged_prompt_contract(self) -> None:
        prompt = PromptLoader().load("score_opportunities")

        assert prompt.metadata.name == "score_opportunities"
        assert prompt.variables == {"workflows_digest"}

    async def test_agent_renders_digest_and_parses(self, db_session) -> None:
        workflows = await (await _seed_workflows(db_session)).list_details()
        provider = FakeProvider(_score_payload((1, {})))
        agent = OpportunityScoringAgent(
            provider=provider, prompt=PromptLoader().load("score_opportunities")
        )

        output = await agent.run(OpportunityScoringInput(workflows=workflows))

        assert output.scores[0].pain_intensity.score == 5
        request = provider.requests[0]
        assert "[1] Workflow" in request.prompt
        assert "Steps: step one; step two" in request.prompt

    async def test_out_of_range_dimension_score_fails_validation(self) -> None:
        bad = _score_payload((1, {})).replace('"score": 5', '"score": 11', 1)
        agent = OpportunityScoringAgent(
            provider=FakeProvider(bad), prompt=PromptLoader().load("score_opportunities")
        )

        with pytest.raises(AgentExecutionError, match=r"\[opportunity_scoring\]"):
            await agent.run(OpportunityScoringInput(workflows=[]))

    async def test_eval_fixtures_run_through_the_harness(self) -> None:
        prompt = PromptLoader().load("score_opportunities")
        cases = PromptLoader().load_eval_cases("score_opportunities")
        target = prompt_completion_target(prompt, FakeProvider('{"scores": []}'))

        report = await run_eval_cases(target, cases)

        assert report.passed is True


class TestServiceAndRuntime:
    async def test_score_ranks_persists_and_drops_invalid_index(self, db_session) -> None:
        await _seed_workflows(db_session, count=2)
        payload = _score_payload(
            (1, {"pain": 3, "auto": 3, "freq": 3, "market": 3, "pay": 3}),
            (2, {"pain": 9, "auto": 9, "freq": 9, "market": 9, "pay": 9}),
            (99, {}),  # invalid index — dropped entirely
        )
        service = OpportunityScoringService(
            agent=OpportunityScoringAgent(
                provider=FakeProvider(payload),
                prompt=PromptLoader().load("score_opportunities"),
            ),
            workflow_repository=WorkflowRepository(db_session),
            opportunity_repository=OpportunityRepository(db_session),
        )

        report = await service.score(limit=10)

        assert report.workflows_scored == 2
        # Ranked best-first: workflow 2 (all 9s) above workflow 1 (all 3s).
        assert report.opportunities[0].total_score == 90.0
        assert report.opportunities[1].total_score == 30.0

        rows = await OpportunityRepository(db_session).list_all()
        assert len(rows) == 2
        assert {row.total_score for row in rows} == {30.0, 90.0}
        assert rows[0].dimensions["pain_intensity"]["rationale"] == "grounded reason"

    async def test_no_workflows_skips_the_agent(self, db_session) -> None:
        provider = FakeProvider("{}")
        service = OpportunityScoringService(
            agent=OpportunityScoringAgent(
                provider=provider, prompt=PromptLoader().load("score_opportunities")
            ),
            workflow_repository=WorkflowRepository(db_session),
            opportunity_repository=OpportunityRepository(db_session),
        )

        report = await service.score()

        assert report.workflows_scored == 0
        assert provider.requests == []

    async def test_end_to_end_on_sqlite(self, db_engine: AsyncEngine) -> None:
        factory = create_session_factory(db_engine)
        async with factory() as session:
            await _seed_workflows(session, count=1)
            await session.commit()

        report, markdown = await run_opportunity_scoring(
            limit=10,
            settings=Settings(_env_file=None),
            engine=db_engine,
            provider=FakeProvider(_score_payload((1, {"pain": 8}))),
        )

        assert report.workflows_scored == 1
        assert "# Opportunity Scoring Report" in markdown
        assert "## 1. Workflow 1 —" in markdown
        assert "**Pain intensity:** 8/10" in markdown

    async def test_report_renders_empty_state(self) -> None:
        from ai_oip.schemas import OpportunityReport

        markdown = render_opportunity_report(
            OpportunityReport(workflows_scored=0, opportunities=[])
        )

        assert "_No workflows were available to score._" in markdown


class TestUnifiedCli:
    def test_parser_covers_all_three_stages(self) -> None:
        from pathlib import Path

        from ai_oip.runtime.cli import build_parser

        parser = build_parser()

        discover = parser.parse_args(["discover", "automation pain", "--limit", "5"])
        assert (discover.command, discover.query, discover.limit) == (
            "discover",
            "automation pain",
            5,
        )

        workflows = parser.parse_args(["workflows"])
        assert (workflows.command, workflows.limit) == ("workflows", 50)

        score = parser.parse_args(["score", "--output", "opps.md"])
        assert (score.command, score.limit, score.output) == ("score", 20, Path("opps.md"))

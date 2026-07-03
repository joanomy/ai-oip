"""Tests for M12: product recommendation — three-store read gated on
competition research, honesty-constrained agent, persistence, runtime,
eval fixtures."""

import json

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from ai_oip.agents.product_recommendation import ProductRecommendationAgent
from ai_oip.config import Settings
from ai_oip.core.exceptions import AgentExecutionError
from ai_oip.evals import prompt_completion_target, run_eval_cases
from ai_oip.models import create_session_factory
from ai_oip.prompts import PromptLoader
from ai_oip.repositories import (
    CompetitionRepository,
    OpportunityRepository,
    ProductRecommendationRepository,
    WorkflowRepository,
)
from ai_oip.runtime.product_recommendation import run_product_recommendation
from ai_oip.schemas import (
    Competitor,
    DimensionScore,
    DiscoveredWorkflow,
    ProductRecommendationInput,
    RecommendationTarget,
    WorkflowCompetition,
    WorkflowScore,
)
from ai_oip.services import ProductRecommendationService, render_recommendation_report
from tests.fixtures.fakes import FakeProvider

PLAN_OUTPUT = json.dumps(
    {
        "plans": [
            {
                "workflow_index": 1,
                "recommendation": "build",
                "product_concept": "A guided invoice intake tool.",
                "mvp_scope": ["Upload PDF", "Auto-extract fields", "One-click reconcile"],
                "differentiation": "SMB pricing with reconciliation built in.",
                "rationale": "Low saturation, high score, clear gap.",
            },
            {
                "workflow_index": 99,
                "recommendation": "pass",
                "product_concept": "n/a",
                "mvp_scope": [],
                "differentiation": None,
                "rationale": "n/a",
            },
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


async def _seed_researched_workflow(
    session: AsyncSession, *, score_value: int, saturation: str = "low"
) -> None:
    """Seed one workflow + opportunity score + competition assessment."""
    workflow_repo = WorkflowRepository(session)
    opportunity_repo = OpportunityRepository(session)
    competition_repo = CompetitionRepository(session)
    await workflow_repo.add_discovered(
        DiscoveredWorkflow(
            name="Workflow", description="Description", steps=["step"], actors=["A"]
        ),
        problem_ids=[],
    )
    details = await workflow_repo.list_details(limit=1)
    await opportunity_repo.add_score(
        workflow=details[0],
        score=_uniform_score(1, score_value),
        total_score=float(score_value * 10),
    )
    await competition_repo.add_assessment(
        WorkflowCompetition(
            workflow_index=1,
            competitors=[Competitor(name="Acme OCR", offering="Extraction", positioning=None)],
            market_gap="No SMB-priced option.",
            saturation=saturation,  # type: ignore[arg-type]
        ),
        workflow_id=details[0].id,
        workflow_name=details[0].name,
    )


def _service(db_session: AsyncSession, provider: FakeProvider) -> ProductRecommendationService:
    return ProductRecommendationService(
        agent=ProductRecommendationAgent(
            provider=provider, prompt=PromptLoader().load("product_recommendation")
        ),
        opportunity_repository=OpportunityRepository(db_session),
        workflow_repository=WorkflowRepository(db_session),
        competition_repository=CompetitionRepository(db_session),
        recommendation_repository=ProductRecommendationRepository(db_session),
    )


class TestPromptAndAgent:
    async def test_packaged_prompt_contract(self) -> None:
        prompt = PromptLoader().load("product_recommendation")

        assert prompt.metadata.name == "product_recommendation"
        assert prompt.variables == {"targets_digest"}
        # The "not everything is a build" honesty constraint is load-bearing — pin it.
        assert "Do not recommend" in "\n".join(prompt.metadata.validation_rules)

    async def test_agent_renders_digest_and_parses(self, db_session) -> None:
        await _seed_researched_workflow(db_session, score_value=8, saturation="low")
        details = await WorkflowRepository(db_session).list_details()
        competition = await CompetitionRepository(db_session).get_latest_by_workflow(details[0].id)
        assert competition is not None
        provider = FakeProvider(PLAN_OUTPUT)
        agent = ProductRecommendationAgent(
            provider=provider, prompt=PromptLoader().load("product_recommendation")
        )

        output = await agent.run(
            ProductRecommendationInput(
                targets=[
                    RecommendationTarget(
                        workflow=details[0], total_score=80.0, competition=competition
                    )
                ]
            )
        )

        assert output.plans[0].recommendation == "build"
        request = provider.requests[0]
        assert "(opportunity score 80.0/100)" in request.prompt
        assert "saturation low" in request.prompt

    async def test_invalid_recommendation_fails_validation(self) -> None:
        bad = PLAN_OUTPUT.replace('"build"', '"maybe"', 1)
        agent = ProductRecommendationAgent(
            provider=FakeProvider(bad), prompt=PromptLoader().load("product_recommendation")
        )

        with pytest.raises(AgentExecutionError, match=r"\[product_recommendation\]"):
            await agent.run(ProductRecommendationInput(targets=[]))

    async def test_eval_fixtures_run_through_the_harness(self) -> None:
        prompt = PromptLoader().load("product_recommendation")
        cases = PromptLoader().load_eval_cases("product_recommendation")
        target = prompt_completion_target(prompt, FakeProvider('{"plans": []}'))

        report = await run_eval_cases(target, cases)

        assert report.passed is True


class TestService:
    async def test_recommend_persists_and_drops_invalid_index(self, db_session) -> None:
        await _seed_researched_workflow(db_session, score_value=9)
        service = _service(db_session, FakeProvider(PLAN_OUTPUT))

        report = await service.recommend(limit=5)

        assert report.targets_analyzed == 1
        assert len(report.recommendations) == 1  # index 99 dropped
        rec = report.recommendations[0]
        assert rec.recommendation == "build"
        assert rec.mvp_scope == ["Upload PDF", "Auto-extract fields", "One-click reconcile"]

        rows = await ProductRecommendationRepository(db_session).list_all()
        assert len(rows) == 1
        assert rows[0].recommendation == "build"
        assert rows[0].mvp_scope == ["Upload PDF", "Auto-extract fields", "One-click reconcile"]

    async def test_unresearched_workflow_is_skipped(self, db_session) -> None:
        # Scored but never run through competition research (M11) — no
        # target should be built for it; nothing to ground a recommendation in.
        workflow_repo = WorkflowRepository(db_session)
        opportunity_repo = OpportunityRepository(db_session)
        await workflow_repo.add_discovered(
            DiscoveredWorkflow(name="W", description="D", steps=[], actors=[]), problem_ids=[]
        )
        detail = (await workflow_repo.list_details())[0]
        await opportunity_repo.add_score(
            workflow=detail, score=_uniform_score(1, 9), total_score=90.0
        )
        provider = FakeProvider(PLAN_OUTPUT)
        service = _service(db_session, provider)

        report = await service.recommend(limit=5)

        assert report.targets_analyzed == 0
        assert provider.requests == []

    async def test_rescored_workflow_is_recommended_once_at_best_score(self, db_session) -> None:
        workflow_repo = WorkflowRepository(db_session)
        opportunity_repo = OpportunityRepository(db_session)
        competition_repo = CompetitionRepository(db_session)
        await workflow_repo.add_discovered(
            DiscoveredWorkflow(name="W", description="D", steps=[], actors=[]), problem_ids=[]
        )
        detail = (await workflow_repo.list_details())[0]
        await opportunity_repo.add_score(
            workflow=detail, score=_uniform_score(1, 5), total_score=50.0
        )
        await opportunity_repo.add_score(
            workflow=detail, score=_uniform_score(1, 8), total_score=80.0
        )
        await competition_repo.add_assessment(
            WorkflowCompetition(
                workflow_index=1, competitors=[], market_gap=None, saturation="low"
            ),
            workflow_id=detail.id,
            workflow_name=detail.name,
        )
        provider = FakeProvider(PLAN_OUTPUT)
        service = _service(db_session, provider)

        report = await service.recommend(limit=5)

        assert report.targets_analyzed == 1
        assert report.recommendations[0].total_score == 80.0

    async def test_no_scores_skips_the_agent(self, db_session) -> None:
        provider = FakeProvider("{}")
        service = _service(db_session, provider)

        report = await service.recommend()

        assert report.targets_analyzed == 0
        assert provider.requests == []


class TestRuntimeAndReport:
    async def test_end_to_end_on_sqlite(self, db_engine: AsyncEngine) -> None:
        factory = create_session_factory(db_engine)
        async with factory() as session:
            await _seed_researched_workflow(session, score_value=7)
            await session.commit()

        report, markdown = await run_product_recommendation(
            limit=5,
            settings=Settings(_env_file=None),
            engine=db_engine,
            provider=FakeProvider(PLAN_OUTPUT),
        )

        assert report.targets_analyzed == 1
        assert "# Product Recommendation Report" in markdown
        assert "BUILD" in markdown
        assert "Upload PDF" in markdown
        assert "SMB pricing with reconciliation built in." in markdown

    async def test_report_renders_empty_state(self) -> None:
        from ai_oip.schemas import RecommendationReport

        markdown = render_recommendation_report(
            RecommendationReport(targets_analyzed=0, recommendations=[])
        )

        assert "_No researched opportunities were available to recommend on._" in markdown

    def test_cli_has_recommend_subcommand(self) -> None:
        from ai_oip.runtime.cli import build_parser

        args = build_parser().parse_args(["recommend", "--limit", "3"])

        assert (args.command, args.limit) == ("recommend", 3)

"""Tests for M9: workflow discovery — agent, repositories, service,
runtime entrypoint, and the prompt's eval fixtures through the harness."""

import json

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from ai_oip.agents.workflow_discovery import WorkflowDiscoveryAgent
from ai_oip.config import Settings
from ai_oip.core.exceptions import AgentExecutionError, ConfigurationError
from ai_oip.evals import prompt_completion_target, run_eval_cases
from ai_oip.models import create_session_factory
from ai_oip.prompts import PromptLoader
from ai_oip.repositories import ProblemRepository, WorkflowRepository
from ai_oip.runtime.workflows import run_workflow_discovery
from ai_oip.schemas import ExtractedProblem, WorkflowDiscoveryInput
from ai_oip.services import WorkflowDiscoveryService, render_workflow_report
from tests.fixtures.fakes import FakeProvider, make_item

pytestmark = pytest.mark.asyncio

WORKFLOW_OUTPUT = json.dumps(
    {
        "workflows": [
            {
                "name": "Vendor invoice data entry",
                "description": "Manually transferring invoice data from PDFs into accounting.",
                "steps": ["Open vendor PDF", "Re-key fields", "Reconcile totals"],
                "actors": ["Bookkeeper"],
                "problem_indexes": [1, 99],  # 99 out of range — dropped
            }
        ]
    }
)


async def _seed_problems(session: AsyncSession, count: int = 2) -> ProblemRepository:
    repo = ProblemRepository(session)
    for index in range(1, count + 1):
        await repo.add_extracted(
            ExtractedProblem(
                description=f"Problem number {index}",
                context="Accounting",
                evidence=f"evidence {index}",
            ),
            source_item=make_item(index),
            collector_name="hackernews",
        )
    return repo


@pytest.fixture
def prompt():
    return PromptLoader().load("discover_workflows")


class TestPromptAndAgent:
    async def test_packaged_prompt_contract(self, prompt) -> None:
        assert prompt.metadata.name == "discover_workflows"
        assert prompt.metadata.input_schema == "WorkflowDiscoveryInput"
        assert prompt.metadata.output_schema == "WorkflowDiscoveryOutput"
        assert prompt.variables == {"problems_digest"}

    async def test_agent_renders_digest_and_parses(self, prompt, db_session) -> None:
        problems = await (await _seed_problems(db_session)).list_details()
        provider = FakeProvider(WORKFLOW_OUTPUT)
        agent = WorkflowDiscoveryAgent(provider=provider, prompt=prompt)

        output = await agent.run(WorkflowDiscoveryInput(problems=problems))

        assert output.workflows[0].name == "Vendor invoice data entry"
        request = provider.requests[0]
        assert request.system == prompt.metadata.role
        assert "[1] Problem number" in request.prompt
        assert 'Evidence: "evidence' in request.prompt

    async def test_bad_output_raises_agent_execution_error(self, prompt) -> None:
        agent = WorkflowDiscoveryAgent(provider=FakeProvider("nope"), prompt=prompt)

        with pytest.raises(AgentExecutionError, match=r"\[workflow_discovery\]"):
            await agent.run(WorkflowDiscoveryInput(problems=[]))

    async def test_eval_fixtures_run_through_the_harness(self, prompt) -> None:
        cases = PromptLoader().load_eval_cases("discover_workflows")
        target = prompt_completion_target(prompt, FakeProvider('{"workflows": []}'))

        report = await run_eval_cases(target, cases)

        assert report.passed is True
        assert len(report.results) == 2


class TestRepositories:
    async def test_list_details_returns_schemas_newest_first(self, db_session) -> None:
        repo = await _seed_problems(db_session, count=3)

        details = await repo.list_details(limit=2)

        assert len(details) == 2
        assert all(detail.source == "hackernews" for detail in details)
        assert details[0].description.startswith("Problem number")

    async def test_add_discovered_persists_with_problem_ids(self, db_session) -> None:
        problem_repo = await _seed_problems(db_session, count=1)
        details = await problem_repo.list_details()
        workflow_repo = WorkflowRepository(db_session)
        from ai_oip.schemas import DiscoveredWorkflow

        await workflow_repo.add_discovered(
            DiscoveredWorkflow(
                name="Invoice entry",
                description="Re-keying PDFs.",
                steps=["a", "b"],
                actors=["Bookkeeper"],
                problem_indexes=[1],
            ),
            problem_ids=[details[0].id],
        )

        rows = await workflow_repo.list_all()
        assert len(rows) == 1
        assert rows[0].steps == ["a", "b"]
        assert rows[0].problem_ids == [str(details[0].id)]


class TestService:
    async def test_discover_links_valid_indexes_and_drops_invalid(self, db_session) -> None:
        await _seed_problems(db_session, count=2)
        provider = FakeProvider(WORKFLOW_OUTPUT)
        service = WorkflowDiscoveryService(
            agent=WorkflowDiscoveryAgent(
                provider=provider, prompt=PromptLoader().load("discover_workflows")
            ),
            problem_repository=ProblemRepository(db_session),
            workflow_repository=WorkflowRepository(db_session),
        )

        report = await service.discover(limit=10)

        assert report.problems_analyzed == 2
        assert len(report.workflows) == 1
        assert report.workflows[0].problems_linked == 1  # index 99 dropped

        rows = await WorkflowRepository(db_session).list_all()
        assert len(rows) == 1
        assert len(rows[0].problem_ids) == 1

    async def test_no_stored_problems_skips_the_agent(self, db_session) -> None:
        provider = FakeProvider("{}")
        service = WorkflowDiscoveryService(
            agent=WorkflowDiscoveryAgent(
                provider=provider, prompt=PromptLoader().load("discover_workflows")
            ),
            problem_repository=ProblemRepository(db_session),
            workflow_repository=WorkflowRepository(db_session),
        )

        report = await service.discover()

        assert report.problems_analyzed == 0
        assert report.workflows == []
        assert provider.requests == []


class TestRuntimeAndReport:
    async def test_end_to_end_on_sqlite(self, db_engine: AsyncEngine) -> None:
        factory = create_session_factory(db_engine)
        async with factory() as session:
            await _seed_problems(session, count=2)
            await session.commit()

        report, markdown = await run_workflow_discovery(
            limit=10,
            settings=Settings(_env_file=None),
            engine=db_engine,
            provider=FakeProvider(WORKFLOW_OUTPUT),
        )

        assert report.problems_analyzed == 2
        assert "# Workflow Discovery Report" in markdown
        assert "## 1. Vendor invoice data entry" in markdown
        assert "1. Open vendor PDF" in markdown
        assert "**Actors:** Bookkeeper" in markdown
        assert "_Linked problems: 1_" in markdown

    async def test_missing_api_key_fails_fast(self, db_engine: AsyncEngine) -> None:
        with pytest.raises(ConfigurationError, match="requires an API key"):
            await run_workflow_discovery(settings=Settings(_env_file=None), engine=db_engine)

    async def test_report_renders_empty_state(self) -> None:
        from ai_oip.schemas import WorkflowReport

        markdown = render_workflow_report(WorkflowReport(problems_analyzed=0, workflows=[]))

        assert "_No recurring workflows were identified" in markdown

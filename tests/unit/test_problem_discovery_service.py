"""Tests for ProblemDiscoveryService: the orchestration slice on SQLite."""

import json

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from ai_oip.agents.problem_extraction import ProblemExtractionAgent
from ai_oip.core.exceptions import AgentExecutionError
from ai_oip.prompts import PromptLoader
from ai_oip.repositories import ProblemRepository
from ai_oip.services import ProblemDiscoveryService, render_markdown_report
from tests.fixtures.fakes import FakeCollector, FakeProvider, make_item

pytestmark = pytest.mark.asyncio

TWO_PROBLEMS = json.dumps(
    {
        "problems": [
            {
                "description": "Manual invoice entry wastes hours.",
                "context": "Accounting",
                "evidence": "two hours every week",
                "source_index": 1,
            },
            {
                "description": "No good way to monitor cron failures.",
                "context": None,
                "evidence": "jobs fail silently",
                "source_index": 99,  # out of range — degrades to collector attribution
            },
        ]
    }
)


def _service(db_session: AsyncSession, provider: FakeProvider, collector: FakeCollector):
    prompt = PromptLoader().load("extract_problems")
    return ProblemDiscoveryService(
        collector=collector,
        agent=ProblemExtractionAgent(provider=provider, prompt=prompt),
        repository=ProblemRepository(db_session),
    )


async def test_discover_persists_problems_and_builds_report(db_session) -> None:
    collector = FakeCollector([make_item(1), make_item(2)])
    provider = FakeProvider(TWO_PROBLEMS)
    service = _service(db_session, provider, collector)

    report = await service.discover("automation pain", limit=10)

    assert report.query == "automation pain"
    assert report.source == "fake-source"
    assert report.items_collected == 2
    assert len(report.findings) == 2

    # In-range source_index resolves to the item; out-of-range degrades.
    assert report.findings[0].source_title == "Ask HN: item 1"
    assert report.findings[1].source_title is None

    rows = await ProblemRepository(db_session).list_all()
    assert len(rows) == 2
    sources = {row.source_external_id for row in rows}
    assert sources == {"hn-1", None}

    assert collector.queries == [("automation pain", 10)]


async def test_discover_with_no_items_skips_the_agent(db_session) -> None:
    collector = FakeCollector([])
    provider = FakeProvider('{"problems": []}')
    service = _service(db_session, provider, collector)

    report = await service.discover("nothing")

    assert report.items_collected == 0
    assert report.findings == []
    assert provider.requests == []  # no model call without signal


async def test_agent_failure_propagates(db_session) -> None:
    collector = FakeCollector([make_item(1)])
    provider = FakeProvider("not json")
    service = _service(db_session, provider, collector)

    with pytest.raises(AgentExecutionError):
        await service.discover("x")


async def test_markdown_report_renders_findings(db_session) -> None:
    collector = FakeCollector([make_item(1)])
    provider = FakeProvider(TWO_PROBLEMS)
    service = _service(db_session, provider, collector)

    report = await service.discover("automation pain")
    markdown = render_markdown_report(report)

    assert "# Problem Discovery Report" in markdown
    assert "**Problems found:** 2" in markdown
    assert "## 1. Manual invoice entry wastes hours." in markdown
    assert "> two hours every week" in markdown
    assert "https://news.ycombinator.com/item?id=1" in markdown


async def test_markdown_report_handles_zero_findings(db_session) -> None:
    collector = FakeCollector([])
    service = _service(db_session, FakeProvider("{}"), collector)

    report = await service.discover("nothing")
    markdown = render_markdown_report(report)

    assert "_No concrete problems were extracted" in markdown

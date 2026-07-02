"""Tests for the composition root: the full skeleton wired end-to-end
(fakes at the network edges, everything else real, SQLite at rest)."""

import json

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine

from ai_oip.config import Settings
from ai_oip.core.exceptions import ConfigurationError
from ai_oip.models import create_session_factory
from ai_oip.repositories import ProblemRepository
from ai_oip.runtime.skeleton import run_skeleton
from tests.fixtures.fakes import FakeCollector, FakeProvider, make_item

pytestmark = pytest.mark.asyncio

OUTPUT = json.dumps(
    {
        "problems": [
            {
                "description": "Cron jobs fail silently.",
                "context": "Ops",
                "evidence": "jobs fail silently and nobody notices",
                "source_index": 1,
            }
        ]
    }
)

SETTINGS = Settings(_env_file=None)


async def test_skeleton_runs_end_to_end(db_engine: AsyncEngine) -> None:
    report, markdown = await run_skeleton(
        "cron monitoring",
        limit=5,
        settings=SETTINGS,
        engine=db_engine,
        provider=FakeProvider(OUTPUT),
        collector=FakeCollector([make_item(1)]),
    )

    assert report.items_collected == 1
    assert len(report.findings) == 1
    assert report.findings[0].description == "Cron jobs fail silently."
    assert "# Problem Discovery Report" in markdown
    assert "Cron jobs fail silently." in markdown

    # The run committed: a fresh session sees the persisted problem.
    factory = create_session_factory(db_engine)
    async with factory() as session:
        rows = await ProblemRepository(session).list_all()
    assert len(rows) == 1
    assert rows[0].source_external_id == "hn-1"


async def test_skeleton_without_api_key_fails_fast(db_engine: AsyncEngine) -> None:
    with pytest.raises(ConfigurationError, match="requires an API key"):
        await run_skeleton(
            "anything",
            settings=SETTINGS,  # no anthropic_api_key
            engine=db_engine,
            collector=FakeCollector([]),
        )


async def test_injected_engine_is_not_disposed(db_engine: AsyncEngine) -> None:
    await run_skeleton(
        "q",
        settings=SETTINGS,
        engine=db_engine,
        provider=FakeProvider('{"problems": []}'),
        collector=FakeCollector([]),
    )

    # Engine still usable after the run — the skeleton must not dispose
    # an engine it doesn't own.
    factory = create_session_factory(db_engine)
    async with factory() as session:
        assert await ProblemRepository(session).list_all() == []

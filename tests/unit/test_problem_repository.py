"""Tests for ProblemRepository: schemas in, ORM stays inside."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from ai_oip.repositories import ProblemRepository
from ai_oip.schemas import ExtractedProblem
from tests.fixtures.fakes import make_item

pytestmark = pytest.mark.asyncio

PROBLEM = ExtractedProblem(
    description="Invoice data entry is manual and slow.",
    context="Back office",
    evidence="two hours, every week",
    source_index=1,
)


async def test_add_extracted_with_source_item(db_session: AsyncSession) -> None:
    repo = ProblemRepository(db_session)
    item = make_item(7)

    await repo.add_extracted(PROBLEM, source_item=item, collector_name="hackernews")

    rows = await repo.list_all()
    assert len(rows) == 1
    row = rows[0]
    assert row.description == PROBLEM.description
    assert row.context == "Back office"
    assert row.evidence == "two hours, every week"
    assert row.source == "hackernews"
    assert row.source_external_id == "hn-7"
    assert row.source_title == "Ask HN: item 7"
    assert row.source_url == "https://news.ycombinator.com/item?id=7"
    assert row.id is not None
    assert row.created_at is not None


async def test_add_extracted_without_source_item_attributes_collector(
    db_session: AsyncSession,
) -> None:
    repo = ProblemRepository(db_session)

    await repo.add_extracted(PROBLEM, source_item=None, collector_name="hackernews")

    row = (await repo.list_all())[0]
    assert row.source == "hackernews"
    assert row.source_external_id is None
    assert row.source_title is None
    assert row.source_url is None

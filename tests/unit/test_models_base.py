"""Tests for the shared declarative Base and mixins."""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from tests.fixtures.models import DemoRecord

pytestmark = pytest.mark.asyncio


async def test_uuid_primary_key_is_auto_generated(db_session: AsyncSession) -> None:
    record = DemoRecord(value="test")

    db_session.add(record)
    await db_session.flush()

    assert isinstance(record.id, uuid.UUID)


async def test_timestamps_are_set_on_insert(db_session: AsyncSession) -> None:
    record = DemoRecord(value="test")

    db_session.add(record)
    await db_session.flush()
    await db_session.refresh(record)

    assert record.created_at is not None
    assert record.updated_at is not None

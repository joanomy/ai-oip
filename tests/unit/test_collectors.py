"""Tests for the collector framework and the Hacker News collector.

The HTTP client is faked at the httpx boundary — these prove payload
mapping, limit passing, and error wrapping, not the network.
"""

from types import SimpleNamespace

import httpx
import pytest

from ai_oip.collectors import BaseCollector, HackerNewsCollector
from ai_oip.core.exceptions import CollectorError
from ai_oip.schemas import CollectedItem

pytestmark = pytest.mark.asyncio

HIT = {
    "objectID": "40001234",
    "title": "Ask HN: What tedious task do you wish was automated?",
    "url": "https://news.ycombinator.com/item?id=40001234",
    "author": "pg",
    "created_at": "2026-06-30T12:00:00Z",
    "story_text": "Tell me your pain.",
    "points": 321,
    "num_comments": 456,
    "_extra_field_we_ignore": True,
}


class FakeResponse:
    def __init__(self, payload, status_code: int = 200):
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                "error", request=SimpleNamespace(), response=SimpleNamespace()
            )

    def json(self):
        return self._payload


class FakeClient:
    def __init__(self, payload=None, status_code: int = 200, error: Exception | None = None):
        self.payload = payload
        self.status_code = status_code
        self.error = error
        self.calls: list[dict] = []

    async def get(self, url: str, params: dict):
        self.calls.append({"url": url, "params": params})
        if self.error is not None:
            raise self.error
        return FakeResponse(self.payload, self.status_code)


async def test_collect_maps_hits_to_collected_items() -> None:
    client = FakeClient(payload={"hits": [HIT]})
    collector = HackerNewsCollector(client=client)

    items = await collector.collect("automation pain", limit=5)

    assert isinstance(collector, BaseCollector)
    assert len(items) == 1
    item = items[0]
    assert isinstance(item, CollectedItem)
    assert item.source == "hackernews"
    assert item.external_id == "40001234"
    assert item.title.startswith("Ask HN")
    assert item.url == "https://news.ycombinator.com/item?id=40001234"
    assert item.text == "Tell me your pain."
    assert item.author == "pg"
    assert item.created_at.year == 2026
    assert item.metadata == {"points": 321, "num_comments": 456}

    call = client.calls[0]
    assert call["params"]["query"] == "automation pain"
    assert call["params"]["hitsPerPage"] == 5
    assert call["params"]["tags"] == "story"


async def test_missing_title_gets_placeholder() -> None:
    hit = {**HIT, "title": None}
    collector = HackerNewsCollector(client=FakeClient(payload={"hits": [hit]}))

    items = await collector.collect("x")

    assert items[0].title == "(untitled)"


async def test_http_error_is_wrapped_in_collector_error() -> None:
    client = FakeClient(error=httpx.ConnectError("no network"))
    collector = HackerNewsCollector(client=client)

    with pytest.raises(CollectorError, match="Hacker News search failed"):
        await collector.collect("x")


async def test_http_status_error_is_wrapped() -> None:
    collector = HackerNewsCollector(client=FakeClient(payload={}, status_code=503))

    with pytest.raises(CollectorError, match="Hacker News search failed"):
        await collector.collect("x")


async def test_payload_without_hits_list_raises() -> None:
    collector = HackerNewsCollector(client=FakeClient(payload={"unexpected": "shape"}))

    with pytest.raises(CollectorError, match="unexpected payload shape"):
        await collector.collect("x")


async def test_malformed_hit_raises_collector_error() -> None:
    bad_hit = {"title": "no objectID or created_at"}
    collector = HackerNewsCollector(client=FakeClient(payload={"hits": [bad_hit]}))

    with pytest.raises(CollectorError, match="failed validation"):
        await collector.collect("x")


async def test_default_client_is_constructed_when_none_injected() -> None:
    collector = HackerNewsCollector()

    assert isinstance(collector._client, httpx.AsyncClient)
    await collector._client.aclose()

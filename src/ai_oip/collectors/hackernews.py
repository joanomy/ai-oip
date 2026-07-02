"""Hacker News collector, via the Algolia HN Search API.

First concrete collector, chosen deliberately (see the collector-
framework ADR): the API is keyless — no OAuth, no secrets, works
unmodified in CI — and HN discussion (especially "Ask HN") is dense
with people describing real workflow pain, which is exactly the raw
signal the Problem Extraction agent consumes.

The HTTP client is injectable so tests exercise the payload mapping
and error handling against canned responses — same pattern as
`AnthropicProvider`.
"""

from datetime import datetime

import httpx
from pydantic import BaseModel, ConfigDict, ValidationError

from ai_oip.collectors.base import BaseCollector
from ai_oip.core.exceptions import CollectorError
from ai_oip.schemas import CollectedItem

_SEARCH_URL = "https://hn.algolia.com/api/v1/search"


class _HNHit(BaseModel):
    """The subset of an Algolia HN hit we consume — extras ignored."""

    model_config = ConfigDict(extra="ignore", frozen=True)

    objectID: str
    created_at: datetime
    title: str | None = None
    url: str | None = None
    author: str | None = None
    story_text: str | None = None
    points: int | None = None
    num_comments: int | None = None


class HackerNewsCollector(BaseCollector):
    """Collects HN stories matching a search query."""

    name = "hackernews"

    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self._client = client if client is not None else httpx.AsyncClient(timeout=30.0)

    async def collect(self, query: str, *, limit: int = 20) -> list[CollectedItem]:
        try:
            response = await self._client.get(
                _SEARCH_URL,
                params={"query": query, "tags": "story", "hitsPerPage": limit},
            )
            response.raise_for_status()
            payload = response.json()
        except httpx.HTTPError as exc:
            raise CollectorError(f"Hacker News search failed: {exc}") from exc

        hits = payload.get("hits") if isinstance(payload, dict) else None
        if not isinstance(hits, list):
            raise CollectorError(
                "Hacker News search returned an unexpected payload shape (no 'hits' list)"
            )
        return [self._to_item(hit) for hit in hits]

    def _to_item(self, raw_hit: object) -> CollectedItem:
        try:
            hit = _HNHit.model_validate(raw_hit)
        except ValidationError as exc:
            raise CollectorError(f"Hacker News hit failed validation: {exc}") from exc
        return CollectedItem(
            source=self.name,
            external_id=hit.objectID,
            title=hit.title or "(untitled)",
            url=hit.url,
            text=hit.story_text,
            author=hit.author,
            created_at=hit.created_at,
            metadata={"points": hit.points, "num_comments": hit.num_comments},
        )

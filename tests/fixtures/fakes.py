"""Shared fakes for exercising the pipeline without network or model."""

from datetime import UTC, datetime

from ai_oip.collectors import BaseCollector
from ai_oip.providers import (
    CompletionRequest,
    CompletionResponse,
    LLMProvider,
    TokenUsage,
)
from ai_oip.schemas import CollectedItem


def make_item(index: int = 1, *, text: str | None = "Some body text.") -> CollectedItem:
    return CollectedItem(
        source="hackernews",
        external_id=f"hn-{index}",
        title=f"Ask HN: item {index}",
        url=f"https://news.ycombinator.com/item?id={index}",
        text=text,
        author="someone",
        created_at=datetime(2026, 6, 30, tzinfo=UTC),
    )


class FakeProvider(LLMProvider):
    """Returns canned text (and optionally sources); records every request it receives."""

    name = "fake"

    def __init__(self, text: str, *, sources: tuple[str, ...] = ()) -> None:
        self.text = text
        self.sources = sources
        self.requests: list[CompletionRequest] = []

    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        self.requests.append(request)
        return CompletionResponse(
            text=self.text,
            model="fake-model",
            stop_reason="end_turn",
            usage=TokenUsage(input_tokens=10, output_tokens=20),
            sources=self.sources,
        )


class FakeCollector(BaseCollector):
    """Returns preset items; records queries."""

    name = "fake-source"

    def __init__(self, items: list[CollectedItem]) -> None:
        self.items = items
        self.queries: list[tuple[str, int]] = []

    async def collect(self, query: str, *, limit: int = 20) -> list[CollectedItem]:
        self.queries.append((query, limit))
        return self.items[:limit]

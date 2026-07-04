"""Tests for the LLM provider abstraction and the Anthropic implementation.

The Anthropic client is faked at the SDK boundary — these tests prove
the request/response mapping, error wrapping, and fail-fast key
handling, not the network.
"""

from types import SimpleNamespace

import anthropic
import pytest
from pydantic import SecretStr

from ai_oip.config import Settings
from ai_oip.core.exceptions import ConfigurationError, ProviderError
from ai_oip.providers import (
    AnthropicProvider,
    CompletionRequest,
    CompletionResponse,
    LLMProvider,
    WebSearchOptions,
    anthropic_provider_from_settings,
)

pytestmark = pytest.mark.asyncio

MODEL = "claude-opus-4-8"


def _stub_response(text: str = "Hello!") -> SimpleNamespace:
    return SimpleNamespace(
        content=[
            SimpleNamespace(type="thinking", thinking=""),
            SimpleNamespace(type="text", text=text),
        ],
        model=MODEL,
        stop_reason="end_turn",
        usage=SimpleNamespace(input_tokens=12, output_tokens=34),
    )


def _web_search_result(url: str) -> SimpleNamespace:
    return SimpleNamespace(type="web_search_result", url=url, title="t", encrypted_content="c")


def _web_search_tool_result(results: list[SimpleNamespace] | SimpleNamespace) -> SimpleNamespace:
    return SimpleNamespace(type="web_search_tool_result", content=results)


class FakeMessages:
    """Returns `response` for every call, or the next of `responses` in order."""

    def __init__(
        self,
        response=None,
        *,
        responses: list[SimpleNamespace] | None = None,
        error: Exception | None = None,
    ):
        self.response = response
        self._responses = iter(responses) if responses is not None else None
        self.error = error
        self.calls: list[dict] = []

    async def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return next(self._responses) if self._responses is not None else self.response


def _provider(messages: FakeMessages) -> AnthropicProvider:
    client = SimpleNamespace(messages=messages)
    return AnthropicProvider(default_model=MODEL, client=client)


async def test_complete_maps_request_and_response() -> None:
    messages = FakeMessages(response=_stub_response("The answer."))
    provider = _provider(messages)

    response = await provider.complete(
        CompletionRequest(prompt="Question?", system="Be brief.", max_tokens=500)
    )

    assert isinstance(provider, LLMProvider)
    assert isinstance(response, CompletionResponse)
    # Text extraction ignores non-text blocks (e.g. thinking).
    assert response.text == "The answer."
    assert response.model == MODEL
    assert response.stop_reason == "end_turn"
    assert response.usage.input_tokens == 12
    assert response.usage.output_tokens == 34
    assert response.usage.total_tokens == 46

    call = messages.calls[0]
    assert call["model"] == MODEL
    assert call["max_tokens"] == 500
    assert call["system"] == "Be brief."
    assert call["thinking"] == {"type": "adaptive"}  # default on
    assert call["messages"] == [{"role": "user", "content": "Question?"}]


async def test_request_model_overrides_provider_default() -> None:
    messages = FakeMessages(response=_stub_response())
    provider = _provider(messages)

    await provider.complete(CompletionRequest(prompt="x", model="claude-haiku-4-5"))

    assert messages.calls[0]["model"] == "claude-haiku-4-5"


async def test_omitted_system_and_disabled_thinking_are_omitted() -> None:
    messages = FakeMessages(response=_stub_response())
    provider = _provider(messages)

    await provider.complete(CompletionRequest(prompt="x", adaptive_thinking=False))

    call = messages.calls[0]
    assert call["system"] is anthropic.omit
    assert call["thinking"] is anthropic.omit


async def test_sdk_errors_are_wrapped_in_provider_error() -> None:
    messages = FakeMessages(error=anthropic.AnthropicError("boom"))
    provider = _provider(messages)

    with pytest.raises(ProviderError, match="Anthropic completion failed"):
        await provider.complete(CompletionRequest(prompt="x"))


async def test_missing_api_key_fails_at_construction() -> None:
    with pytest.raises(ConfigurationError, match="requires an API key"):
        AnthropicProvider(default_model=MODEL)


async def test_provider_from_settings_uses_configured_key_and_model() -> None:
    settings = Settings(
        _env_file=None,
        anthropic_api_key=SecretStr("sk-ant-test"),
        anthropic_model=MODEL,
    )

    provider = anthropic_provider_from_settings(settings)

    assert provider.name == "anthropic"
    assert provider._default_model == MODEL


async def test_provider_from_settings_without_key_fails_fast() -> None:
    settings = Settings(_env_file=None)

    with pytest.raises(ConfigurationError):
        anthropic_provider_from_settings(settings)


class TestWebSearchGrounding:
    """R1 (ADR-0018): the web-search tool mapping and source extraction."""

    async def test_no_web_search_option_omits_tools(self) -> None:
        messages = FakeMessages(response=_stub_response())
        provider = _provider(messages)

        await provider.complete(CompletionRequest(prompt="x"))

        assert messages.calls[0]["tools"] is anthropic.omit

    async def test_web_search_option_declares_the_server_tool(self) -> None:
        messages = FakeMessages(response=_stub_response())
        provider = _provider(messages)

        await provider.complete(
            CompletionRequest(
                prompt="x",
                web_search=WebSearchOptions(max_uses=7, allowed_domains=("example.com",)),
            )
        )

        tools = messages.calls[0]["tools"]
        assert tools == [
            {
                "type": "web_search_20260209",
                "name": "web_search",
                "max_uses": 7,
                "allowed_domains": ["example.com"],
            }
        ]

    async def test_sources_extracted_from_search_result_blocks_deduped(self) -> None:
        response = SimpleNamespace(
            content=[
                _web_search_tool_result(
                    [
                        _web_search_result("https://a.example"),
                        _web_search_result("https://b.example"),
                    ]
                ),
                SimpleNamespace(type="text", text="Answer."),
                _web_search_tool_result([_web_search_result("https://a.example")]),  # dup
            ],
            model=MODEL,
            stop_reason="end_turn",
            usage=SimpleNamespace(input_tokens=1, output_tokens=1),
        )
        messages = FakeMessages(response=response)
        provider = _provider(messages)

        result = await provider.complete(
            CompletionRequest(prompt="x", web_search=WebSearchOptions())
        )

        assert result.sources == ("https://a.example", "https://b.example")

    async def test_search_error_block_yields_no_sources(self) -> None:
        response = SimpleNamespace(
            content=[
                _web_search_tool_result(SimpleNamespace(error_code="max_uses_exceeded")),
                SimpleNamespace(type="text", text="Answer anyway."),
            ],
            model=MODEL,
            stop_reason="end_turn",
            usage=SimpleNamespace(input_tokens=1, output_tokens=1),
        )
        provider = _provider(FakeMessages(response=response))

        result = await provider.complete(
            CompletionRequest(prompt="x", web_search=WebSearchOptions())
        )

        assert result.sources == ()
        assert result.text == "Answer anyway."

    async def test_pause_turn_is_continued_and_usage_accumulates(self) -> None:
        first = SimpleNamespace(
            content=[SimpleNamespace(type="text", text="partial ")],
            model=MODEL,
            stop_reason="pause_turn",
            usage=SimpleNamespace(input_tokens=10, output_tokens=5),
        )
        second = SimpleNamespace(
            content=[SimpleNamespace(type="text", text="rest.")],
            model=MODEL,
            stop_reason="end_turn",
            usage=SimpleNamespace(input_tokens=3, output_tokens=7),
        )
        messages = FakeMessages(responses=[first, second])
        provider = _provider(messages)

        result = await provider.complete(
            CompletionRequest(prompt="x", web_search=WebSearchOptions())
        )

        assert result.text == "partial rest."
        assert result.stop_reason == "end_turn"
        assert result.usage.input_tokens == 13
        assert result.usage.output_tokens == 12
        assert len(messages.calls) == 2
        # Second call echoes the paused assistant turn back unchanged.
        assert messages.calls[1]["messages"][-1] == {
            "role": "assistant",
            "content": first.content,
        }

    async def test_pause_turn_beyond_the_bound_raises_provider_error(self) -> None:
        forever_paused = SimpleNamespace(
            content=[SimpleNamespace(type="text", text="still going")],
            model=MODEL,
            stop_reason="pause_turn",
            usage=SimpleNamespace(input_tokens=1, output_tokens=1),
        )
        # Enough responses for every allowed attempt, all still pausing.
        messages = FakeMessages(responses=[forever_paused] * 10)
        provider = _provider(messages)

        with pytest.raises(ProviderError, match="pause_turn"):
            await provider.complete(CompletionRequest(prompt="x", web_search=WebSearchOptions()))

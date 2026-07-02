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


class FakeMessages:
    def __init__(self, response=None, error: Exception | None = None):
        self.response = response
        self.error = error
        self.calls: list[dict] = []

    async def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return self.response


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

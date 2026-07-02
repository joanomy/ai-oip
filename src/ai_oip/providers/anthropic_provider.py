"""Anthropic implementation of the LLMProvider interface.

The client is injectable so tests exercise the request/response mapping
against a fake — no network, no API key. Production construction goes
through `anthropic_provider_from_settings`, which fails fast with
`ConfigurationError` if no API key is configured (same startup-failure
philosophy as the rest of the config layer).
"""

from anthropic import AnthropicError, AsyncAnthropic, Omit, omit
from anthropic.types import ThinkingConfigAdaptiveParam
from pydantic import SecretStr

from ai_oip.config import Settings
from ai_oip.core.exceptions import ConfigurationError, ProviderError
from ai_oip.providers.base import (
    CompletionRequest,
    CompletionResponse,
    LLMProvider,
    TokenUsage,
)


class AnthropicProvider(LLMProvider):
    """LLMProvider backed by the official Anthropic SDK (async client)."""

    name = "anthropic"

    def __init__(
        self,
        *,
        default_model: str,
        api_key: SecretStr | None = None,
        client: AsyncAnthropic | None = None,
    ) -> None:
        """Create the provider from an API key, or an injected client (tests).

        Raises:
            ConfigurationError: if neither a client nor an API key is given.
        """
        if client is not None:
            self._client = client
        elif api_key is not None:
            self._client = AsyncAnthropic(api_key=api_key.get_secret_value())
        else:
            raise ConfigurationError(
                "AnthropicProvider requires an API key — set ANTHROPIC_API_KEY "
                "(Settings.anthropic_api_key). Refusing to construct a provider "
                "that would fail on first use instead of at startup."
            )
        self._default_model = default_model

    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        system: str | Omit = request.system if request.system is not None else omit
        thinking: ThinkingConfigAdaptiveParam | Omit = (
            ThinkingConfigAdaptiveParam(type="adaptive") if request.adaptive_thinking else omit
        )
        try:
            response = await self._client.messages.create(
                model=request.model or self._default_model,
                max_tokens=request.max_tokens,
                system=system,
                thinking=thinking,
                messages=[{"role": "user", "content": request.prompt}],
            )
        except AnthropicError as exc:
            raise ProviderError(f"Anthropic completion failed: {exc}") from exc

        text = "".join(block.text for block in response.content if block.type == "text")
        return CompletionResponse(
            text=text,
            model=response.model,
            stop_reason=response.stop_reason,
            usage=TokenUsage(
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
            ),
        )


def anthropic_provider_from_settings(settings: Settings) -> AnthropicProvider:
    """Build the production Anthropic provider from validated Settings."""
    return AnthropicProvider(
        default_model=settings.anthropic_model,
        api_key=settings.anthropic_api_key,
    )

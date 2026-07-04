"""Anthropic implementation of the LLMProvider interface.

The client is injectable so tests exercise the request/response mapping
against a fake — no network, no API key. Production construction goes
through `anthropic_provider_from_settings`, which fails fast with
`ConfigurationError` if no API key is configured (same startup-failure
philosophy as the rest of the config layer).

Web-search grounding (R1, ADR-0018) uses Anthropic's *server-side*
search tool: declared on the request, executed on Anthropic's
infrastructure, results returned in the same response — no client-side
tool loop. Two vendor mechanics live here and never escape: the
`pause_turn` continuation (the server-tool loop may pause mid-turn and
must be re-sent to finish) and source-URL extraction from
`web_search_tool_result` blocks.
"""

from typing import Final

from anthropic import AnthropicError, AsyncAnthropic, Omit, omit
from anthropic.types import (
    ContentBlock,
    MessageParam,
    ThinkingConfigAdaptiveParam,
    WebSearchTool20260209Param,
)
from pydantic import SecretStr

from ai_oip.config import Settings
from ai_oip.core.exceptions import ConfigurationError, ProviderError
from ai_oip.providers.base import (
    CompletionRequest,
    CompletionResponse,
    LLMProvider,
    TokenUsage,
)

#: How many times a `pause_turn` response is re-sent before giving up.
#: A bound, not a retry policy: each continuation is real forward
#: progress by the server-side tool loop, but an unbounded loop on a
#: misbehaving response would burn spend invisibly.
_MAX_PAUSE_CONTINUATIONS: Final = 5


def _web_search_tool(request: CompletionRequest) -> list[WebSearchTool20260209Param] | Omit:
    """Map the provider-agnostic grounding options to Anthropic's tool."""
    if request.web_search is None:
        return omit
    tool: WebSearchTool20260209Param = {
        "type": "web_search_20260209",
        "name": "web_search",
        "max_uses": request.web_search.max_uses,
    }
    if request.web_search.allowed_domains is not None:
        tool["allowed_domains"] = list(request.web_search.allowed_domains)
    return [tool]


def _extract_sources(blocks: list[ContentBlock]) -> tuple[str, ...]:
    """Collect the URLs the server-side search actually returned.

    Ground truth from tool-result blocks, never from model text — the
    model cannot fabricate a provenance entry here. Search errors (an
    object `content` instead of a result list) yield no sources rather
    than failing the completion; the text may still be useful.
    """
    seen: dict[str, None] = {}
    for block in blocks:
        if block.type != "web_search_tool_result":
            continue
        if not isinstance(block.content, list):
            continue  # error object (e.g. max_uses_exceeded) — no sources
        for result in block.content:
            seen.setdefault(result.url)
    return tuple(seen)


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
        tools = _web_search_tool(request)

        messages: list[MessageParam] = [{"role": "user", "content": request.prompt}]
        blocks: list[ContentBlock] = []
        input_tokens = 0
        output_tokens = 0
        for _ in range(1 + _MAX_PAUSE_CONTINUATIONS):
            try:
                response = await self._client.messages.create(
                    model=request.model or self._default_model,
                    max_tokens=request.max_tokens,
                    system=system,
                    thinking=thinking,
                    tools=tools,
                    messages=messages,
                )
            except AnthropicError as exc:
                raise ProviderError(f"Anthropic completion failed: {exc}") from exc
            blocks.extend(response.content)
            input_tokens += response.usage.input_tokens
            output_tokens += response.usage.output_tokens
            if response.stop_reason != "pause_turn":
                break
            # Server-side tool loop paused mid-turn: echo the assistant
            # content back unchanged and re-send; the server resumes.
            messages = [*messages, {"role": "assistant", "content": response.content}]
        else:
            raise ProviderError(
                "Anthropic completion still paused after "
                f"{_MAX_PAUSE_CONTINUATIONS} pause_turn continuations — "
                "refusing to keep spending on a turn that will not finish."
            )

        text = "".join(block.text for block in blocks if block.type == "text")
        return CompletionResponse(
            text=text,
            model=response.model,
            stop_reason=response.stop_reason,
            usage=TokenUsage(input_tokens=input_tokens, output_tokens=output_tokens),
            sources=_extract_sources(blocks),
        )


def anthropic_provider_from_settings(settings: Settings) -> AnthropicProvider:
    """Build the production Anthropic provider from validated Settings."""
    return AnthropicProvider(
        default_model=settings.anthropic_model,
        api_key=settings.anthropic_api_key,
    )

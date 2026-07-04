"""LLM provider interface: the seam where AI vendors are swappable.

Every component that needs a model completion depends on `LLMProvider`,
never on a vendor SDK — replacing or adding a provider means one new
implementation of this interface, not a sweep through agent code
(CLAUDE.md: "Design every component so AI providers can be replaced
with minimal code change").

Deliberately minimal: one method, text in / text out plus usage
accounting. Capabilities get added here when a concrete agent actually
needs them, not speculatively — web-search grounding arrived at R1
(ADR-0018) because grounded competition research needed it; streaming
and structured outputs still wait for their first consumer.
"""

from abc import ABC, abstractmethod

from pydantic import BaseModel, ConfigDict, Field


class TokenUsage(BaseModel):
    """Token accounting for one completion — the raw material for cost tracking."""

    model_config = ConfigDict(frozen=True)

    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


class WebSearchOptions(BaseModel):
    """Provider-agnostic web-search grounding options (R1, ADR-0018).

    How a vendor grounds a completion (which tool version, how results
    come back) is that provider's concern; callers only say *that* they
    want grounding and how much of it.
    """

    model_config = ConfigDict(frozen=True)

    max_uses: int = Field(
        default=5,
        ge=1,
        description="Upper bound on searches per completion — the cost knob.",
    )
    allowed_domains: tuple[str, ...] | None = Field(
        default=None,
        description="If set, restrict results to these domains.",
    )


class CompletionRequest(BaseModel):
    """A provider-agnostic completion request.

    No sampling parameters (temperature/top_p) by design — current
    Anthropic models reject them, and prompting is the supported way
    to steer behavior.
    """

    model_config = ConfigDict(frozen=True)

    prompt: str
    system: str | None = None
    model: str | None = Field(
        default=None,
        description="Override the provider's default model for this request.",
    )
    max_tokens: int = Field(default=16000, ge=1)
    adaptive_thinking: bool = Field(
        default=True,
        description=(
            "Let the model decide when and how much to reason before "
            "answering. On by default per current provider guidance."
        ),
    )
    web_search: WebSearchOptions | None = Field(
        default=None,
        description=(
            "Ground the completion in live web search. None means "
            "model knowledge only (the pre-R1 behavior)."
        ),
    )


class CompletionResponse(BaseModel):
    """A provider-agnostic completion result."""

    model_config = ConfigDict(frozen=True)

    text: str
    model: str
    stop_reason: str | None
    usage: TokenUsage
    sources: tuple[str, ...] = Field(
        default=(),
        description=(
            "URLs of web sources the provider actually consulted for a "
            "grounded completion — extracted from tool results by code, "
            "never taken from model output (provenance is a fact, not a "
            "judgment). Empty for ungrounded completions."
        ),
    )


class LLMProvider(ABC):
    """Abstract base class all LLM providers implement.

    Contract: `complete` either returns a `CompletionResponse` or raises
    `ProviderError` — vendor SDK exceptions never escape a provider.
    """

    #: Provider name, used in logs and configuration.
    name: str

    @abstractmethod
    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        """Execute one completion against the underlying model API.

        Raises:
            ProviderError: on any transport or API failure.
        """
        raise NotImplementedError  # pragma: no cover

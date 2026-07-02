"""LLM provider interface: the seam where AI vendors are swappable.

Every component that needs a model completion depends on `LLMProvider`,
never on a vendor SDK — replacing or adding a provider means one new
implementation of this interface, not a sweep through agent code
(CLAUDE.md: "Design every component so AI providers can be replaced
with minimal code change").

Deliberately minimal at this milestone: one method, text in / text out
plus usage accounting. Tool use, streaming, and structured-output
support get added here when a concrete agent actually needs them,
not speculatively.
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


class CompletionResponse(BaseModel):
    """A provider-agnostic completion result."""

    model_config = ConfigDict(frozen=True)

    text: str
    model: str
    stop_reason: str | None
    usage: TokenUsage


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

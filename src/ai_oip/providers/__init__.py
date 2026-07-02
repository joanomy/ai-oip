"""Providers: LLM vendor clients behind a swappable interface.

Agents depend on `LLMProvider`, never on a vendor SDK — adding or
replacing an AI provider is one new implementation of the interface.

Dependency rule: depends on config, core. NEVER on models or
repositories (enforced by import-linter).
"""

from ai_oip.providers.anthropic_provider import (
    AnthropicProvider,
    anthropic_provider_from_settings,
)
from ai_oip.providers.base import (
    CompletionRequest,
    CompletionResponse,
    LLMProvider,
    TokenUsage,
)

__all__ = [
    "AnthropicProvider",
    "CompletionRequest",
    "CompletionResponse",
    "LLMProvider",
    "TokenUsage",
    "anthropic_provider_from_settings",
]

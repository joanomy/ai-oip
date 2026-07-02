"""Problem Extraction agent: collected raw signal in, concrete problems out.

The first concrete agent, following the full framework recipe: one
responsibility, one input schema, one output schema, one versioned
external prompt (`extract_problems`), provider injected, output parsed
through the guardrail. All items go into one batched completion; the
prompt asks for a source_index per problem so provenance survives the
batching.
"""

from collections.abc import Sequence

from ai_oip.agents.base import BaseAgent, parse_json_output
from ai_oip.prompts import PromptTemplate
from ai_oip.providers import CompletionRequest, LLMProvider
from ai_oip.schemas import CollectedItem, ProblemExtractionInput, ProblemExtractionOutput

_MAX_ITEM_TEXT_CHARS = 1500


def _items_digest(items: Sequence[CollectedItem]) -> str:
    """Render collected items as the numbered digest the prompt expects."""
    blocks: list[str] = []
    for index, item in enumerate(items, start=1):
        text = (item.text or "").strip()
        if len(text) > _MAX_ITEM_TEXT_CHARS:
            text = text[:_MAX_ITEM_TEXT_CHARS] + " …[truncated]"
        block = f"[{index}] {item.title}\nURL: {item.url or 'n/a'}"
        if text:
            block += f"\n{text}"
        blocks.append(block)
    return "\n\n".join(blocks)


class ProblemExtractionAgent(BaseAgent[ProblemExtractionInput, ProblemExtractionOutput]):
    """Extracts concrete problems people describe in collected items."""

    name = "problem_extraction"

    def __init__(self, *, provider: LLMProvider, prompt: PromptTemplate) -> None:
        self._provider = provider
        self._prompt = prompt

    async def run(self, input_data: ProblemExtractionInput) -> ProblemExtractionOutput:
        rendered = self._prompt.render(items_digest=_items_digest(input_data.items))
        response = await self._provider.complete(
            CompletionRequest(prompt=rendered, system=self._prompt.metadata.role)
        )
        return parse_json_output(response.text, ProblemExtractionOutput, agent_name=self.name)

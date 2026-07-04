"""PromptedAgent: the standard single-completion agent frame.

Every business agent so far has the same run() shape: build a digest,
render it into the prompt, complete with the prompt's role as system,
parse through the guardrail. This base owns that frame once; concrete
agents supply only their name, digest, template variable, and output
schema (ADR-0014).

Convenience, not contract: `BaseAgent` remains the interface. An agent
that doesn't fit this shape (multi-turn, tool-using) implements
BaseAgent directly and skips this helper.
"""

from abc import abstractmethod

from pydantic import BaseModel

from ai_oip.agents.base.agent import BaseAgent
from ai_oip.agents.base.output import parse_json_output
from ai_oip.prompts import PromptTemplate
from ai_oip.providers import CompletionRequest, CompletionResponse, LLMProvider


class PromptedAgent[InputT: BaseModel, OutputT: BaseModel](BaseAgent[InputT, OutputT]):
    """Base for digest -> render -> complete -> parse agents."""

    #: The prompt-template variable the digest renders into.
    digest_variable: str
    #: The schema the model's JSON output must validate against.
    output_schema: type[OutputT]

    def __init__(self, *, provider: LLMProvider, prompt: PromptTemplate) -> None:
        self._provider = provider
        self._prompt = prompt

    @abstractmethod
    def digest(self, input_data: InputT) -> str:
        """Render this agent's input as the digest its prompt expects."""
        raise NotImplementedError  # pragma: no cover

    def build_request(self, rendered: str) -> CompletionRequest:
        """The completion request this agent sends.

        Override to attach provider options (e.g. web-search grounding,
        R1/ADR-0018) without re-implementing the run frame.
        """
        return CompletionRequest(prompt=rendered, system=self._prompt.metadata.role)

    async def run(self, input_data: InputT) -> OutputT:
        output, _ = await self.run_detailed(input_data)
        return output

    async def run_detailed(self, input_data: InputT) -> tuple[OutputT, CompletionResponse]:
        """Run the frame and also return the raw provider response.

        For callers that need response metadata — grounding sources
        (R1), token usage for cost telemetry (R3). `run()` remains the
        BaseAgent contract; this is the widened view, same execution.
        """
        rendered = self._prompt.render(**{self.digest_variable: self.digest(input_data)})
        response = await self._provider.complete(self.build_request(rendered))
        output = parse_json_output(response.text, self.output_schema, agent_name=self.name)
        return output, response

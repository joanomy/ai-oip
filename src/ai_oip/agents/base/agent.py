"""Base agent interface.

Every agent in this system implements this contract: one typed input,
one typed output, one `run` method. No agent may have more than one
public entrypoint, and no agent may reach into the database or another
agent directly — orchestration is the caller's job (see `services/`
and the `runtime/` stage modules), not the agent's.
"""

from abc import ABC, abstractmethod

from pydantic import BaseModel


class BaseAgent[InputSchema: BaseModel, OutputSchema: BaseModel](ABC):
    """Abstract base class all agents must inherit from.

    Type parameters:
        InputSchema: Pydantic model describing the agent's single input.
        OutputSchema: Pydantic model describing the agent's single output.

    Contract:
        - Exactly one responsibility per agent.
        - Exactly one prompt per agent (loaded via the prompts module,
          never inlined — enforced once prompt management exists).
        - `run` is the only public entrypoint. No other public methods.
        - Agents do not import from `repositories/`. If data is needed,
          it arrives as part of `InputSchema`.
    """

    #: Name of this agent, used for logging and matching against its
    #: prompt file. Must be set by subclasses.
    name: str

    @abstractmethod
    async def run(self, input_data: InputSchema) -> OutputSchema:
        """Execute the agent's single responsibility.

        Args:
            input_data: Validated input matching this agent's InputSchema.

        Returns:
            Validated output matching this agent's OutputSchema.

        Raises:
            AgentExecutionError: On any failure during execution. Agents
                must not raise raw/unhandled exceptions — see
                `ai_oip.core.exceptions`.
        """
        raise NotImplementedError  # pragma: no cover

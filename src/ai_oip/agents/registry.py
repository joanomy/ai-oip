"""Agent registry: name -> agent class lookup.

`BaseAgent.name` has promised "registry lookup" since the interface was
written; this is that registry. Pipelines resolve agents by name (a
configuration value) rather than by import path, which is what lets new
pipelines be assembled by configuration and composition instead of code
changes.

Registration errors (duplicate name, missing name, unknown lookup) are
programmer/configuration mistakes that should explode at import or
startup time — they raise standard ValueError/KeyError rather than the
AIOIPError hierarchy, which is reserved for runtime failure categories
pipelines are expected to catch and handle.
"""

from typing import Any

from ai_oip.agents.base import BaseAgent


class AgentRegistry:
    """Registry mapping agent names to agent classes.

    Not a global singleton — the composition root creates one and
    registers the agents a deployment actually uses.
    """

    def __init__(self) -> None:
        self._agents: dict[str, type[BaseAgent[Any, Any]]] = {}

    def register(self, agent_cls: type[BaseAgent[Any, Any]]) -> type[BaseAgent[Any, Any]]:
        """Register an agent class under its declared name.

        Returns the class unchanged, so this can be used as a decorator.

        Raises:
            ValueError: if the class declares no name, or the name is taken.
        """
        name = getattr(agent_cls, "name", None)
        if not isinstance(name, str) or not name:
            raise ValueError(
                f"{agent_cls.__name__} must declare a non-empty `name` class "
                "attribute before it can be registered"
            )
        if name in self._agents:
            raise ValueError(
                f"An agent named {name!r} is already registered "
                f"({self._agents[name].__name__}); agent names must be unique"
            )
        self._agents[name] = agent_cls
        return agent_cls

    def get(self, name: str) -> type[BaseAgent[Any, Any]]:
        """Look up an agent class by name.

        Raises:
            KeyError: if no agent is registered under `name`.
        """
        try:
            return self._agents[name]
        except KeyError:
            raise KeyError(
                f"No agent registered under {name!r} (registered: {sorted(self._agents)})"
            ) from None

    def names(self) -> list[str]:
        """All registered agent names, sorted."""
        return sorted(self._agents)

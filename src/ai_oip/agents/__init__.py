"""Agents: single-responsibility AI units.

Each agent: one responsibility, one input schema, one output schema, one
prompt. Agents NEVER import repositories or touch the database directly —
if an agent needs data, a service fetches it and passes it in as typed
input. This keeps agents testable in isolation and safe to run
autonomously without hidden side effects.

Agents reach models only through the `providers` interface (constructor
injection), never a vendor SDK directly.

Dependency rule: depends on providers, schemas, prompts, logging, core.
NEVER on repositories or models.
"""

from ai_oip.agents.base import BaseAgent, log_agent_run, parse_json_output
from ai_oip.agents.registry import AgentRegistry

__all__ = ["AgentRegistry", "BaseAgent", "log_agent_run", "parse_json_output"]

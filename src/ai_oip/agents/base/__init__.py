"""Agents.base: the BaseAgent contract plus the shared run-support helpers
every concrete agent uses (output validation, run tracing)."""

from ai_oip.agents.base.agent import BaseAgent
from ai_oip.agents.base.output import parse_json_output
from ai_oip.agents.base.prompted import PromptedAgent
from ai_oip.agents.base.tracing import log_agent_run

__all__ = ["BaseAgent", "PromptedAgent", "log_agent_run", "parse_json_output"]

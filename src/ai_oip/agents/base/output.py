"""Output guardrail: parse and validate an LLM's JSON output against a schema.

Every agent's contract is "typed output out" — this is the enforcement
point between raw model text and that promise. Models frequently wrap
JSON in markdown fences despite instructions; that's handled here once
rather than per-agent.
"""

import json
import re

from pydantic import BaseModel, ValidationError

from ai_oip.core.exceptions import AgentExecutionError

_FENCE_RE = re.compile(r"\A```(?:json)?\s*\n(.*?)\n?```\s*\Z", re.DOTALL)


def parse_json_output[SchemaT: BaseModel](
    raw: str, schema: type[SchemaT], *, agent_name: str
) -> SchemaT:
    """Parse raw model output into a validated instance of `schema`.

    Tolerates a markdown code fence around the JSON (with or without a
    `json` language tag) — a common model behavior — but nothing looser:
    prose around the JSON is a failure, not something to be salvaged
    with heuristics that would mask a misbehaving prompt.

    Raises:
        AgentExecutionError: if the output is not valid JSON or does not
            validate against `schema`.
    """
    text = raw.strip()
    fenced = _FENCE_RE.match(text)
    if fenced is not None:
        text = fenced.group(1)
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise AgentExecutionError(agent_name, f"output is not valid JSON: {exc}") from exc
    try:
        return schema.model_validate(data)
    except ValidationError as exc:
        raise AgentExecutionError(
            agent_name, f"output does not match {schema.__name__}: {exc}"
        ) from exc

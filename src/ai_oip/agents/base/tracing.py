"""Per-agent run tracing: structured start/complete/fail events with timing.

One context manager, used around every agent invocation, so agent runs
are queryable in logs by name, outcome, and duration — the foundation
the autonomous-runtime stages build their observability on. Token/cost
fields are logged by callers from `CompletionResponse.usage` at the
call site, since one agent run may make several provider calls.
"""

import time
from collections.abc import Iterator
from contextlib import contextmanager

from ai_oip.logging import get_logger


@contextmanager
def log_agent_run(agent_name: str) -> Iterator[None]:
    """Log a structured start/complete (or fail) event pair around an agent run.

    Usage:
        with log_agent_run(agent.name):
            result = await agent.run(input_data)

    Exceptions propagate unchanged — this observes, it never swallows.
    """
    logger = get_logger("ai_oip.agents")
    started = time.perf_counter()
    logger.info("agent_run_started", agent_name=agent_name)
    try:
        yield
    except Exception:
        logger.error(
            "agent_run_failed",
            agent_name=agent_name,
            duration_ms=round((time.perf_counter() - started) * 1000, 1),
        )
        raise
    logger.info(
        "agent_run_completed",
        agent_name=agent_name,
        duration_ms=round((time.perf_counter() - started) * 1000, 1),
    )

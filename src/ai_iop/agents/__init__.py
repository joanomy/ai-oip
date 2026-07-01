"""Agents: single-responsibility AI units.

Each agent: one responsibility, one input schema, one output schema, one
prompt. Agents NEVER import repositories or touch the database directly —
if an agent needs data, a service fetches it and passes it in as typed
input. This keeps agents testable in isolation and safe to run
autonomously without hidden side effects.

Dependency rule: depends on schemas, prompts, core. NEVER on repositories.
"""

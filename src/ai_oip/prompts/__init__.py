"""Prompts: versioned prompt templates, external to Python code.

Prompts are never hardcoded as inline strings in agent code. Each prompt
is a file with a name+version, loaded by a prompt loader (built by the
prompt-management milestone).

Dependency rule: depends only on core.
"""

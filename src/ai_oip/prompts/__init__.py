"""Prompts: versioned prompt templates, external to Python code.

Prompts are never hardcoded as inline strings in agent code. Each prompt
is a Markdown file (YAML frontmatter + Jinja2 body) with a name and
version, shipped with eval fixtures, loaded via `PromptLoader` — see
`loader.py` and ADR-0007 for the format.

Dependency rule: depends only on core.
"""

from ai_oip.prompts.loader import (
    PromptEvalCase,
    PromptLoader,
    PromptMetadata,
    PromptTemplate,
)

__all__ = ["PromptEvalCase", "PromptLoader", "PromptMetadata", "PromptTemplate"]

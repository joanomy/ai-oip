"""Runtime: the composition root and application entrypoints.

This package resolves the question deferred since the layering ADR:
who creates engines/sessions and wires repositories, agents, providers,
and collectors together. Answer: this package, and only this package.

`runtime` sits at the very top of the layer stack and is the ONE
deliberate, documented exception to "only repositories access the
database layer" — it may import `models` session machinery because
composition is its entire job (see ADR-0010 and the import-linter
contract comment in pyproject.toml). Nothing else gets to follow this
precedent.
"""

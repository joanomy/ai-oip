"""Config: typed application settings (Pydantic Settings).

Dependency rule: depends only on core. Nothing depends on config except
the application entrypoint and modules that need a specific setting value
passed to them explicitly.
"""

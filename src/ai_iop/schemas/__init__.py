"""Schemas: Pydantic models describing data IN MOTION.

Used for agent inputs/outputs, API request/response bodies, and any
data crossing a module boundary. Never used for database persistence
— see `models/` for that.

Dependency rule: depends only on core.
"""

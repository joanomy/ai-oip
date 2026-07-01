"""Models: SQLAlchemy ORM models describing data AT REST.

Defines how data is stored in the database. Never imported outside of
`repositories/` — no other layer touches the ORM directly.

Dependency rule: depends only on core.
"""

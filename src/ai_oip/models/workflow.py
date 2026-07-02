"""WorkflowRecord: discovered business workflows at rest.

Problem linkage is a JSON list of problem UUIDs (as strings) rather
than a join table — deliberate (ADR-0011): nothing queries "workflows
for problem X" yet, and JSON avoids async lazy-loading complexity.
Normalize into an association table when a milestone actually needs
the relational query, not before.
"""

from sqlalchemy import JSON, Text
from sqlalchemy.orm import Mapped, mapped_column

from ai_oip.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class WorkflowRecord(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """One discovered business workflow, with linked problem ids."""

    __tablename__ = "workflows"

    name: Mapped[str]
    description: Mapped[str] = mapped_column(Text)
    steps: Mapped[list[str]] = mapped_column(JSON)
    actors: Mapped[list[str]] = mapped_column(JSON)
    #: UUIDs of the problems this workflow underlies, as strings.
    problem_ids: Mapped[list[str]] = mapped_column(JSON)

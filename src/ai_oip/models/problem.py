"""ProblemRecord: the first business table — extracted problems at rest.

Source attribution is denormalized (no collected_items table yet):
the walking skeleton stores problems with enough provenance to trace
them back; a normalized raw-signal table appears when a milestone
actually needs to re-read raw items.
"""

from sqlalchemy import Text
from sqlalchemy.orm import Mapped, mapped_column

from ai_oip.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ProblemRecord(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """One extracted problem, with source provenance."""

    __tablename__ = "problems"

    #: Collector/source name (e.g. "hackernews").
    source: Mapped[str]
    source_external_id: Mapped[str | None]
    source_title: Mapped[str | None] = mapped_column(Text)
    source_url: Mapped[str | None]

    description: Mapped[str] = mapped_column(Text)
    context: Mapped[str | None] = mapped_column(Text)
    evidence: Mapped[str | None] = mapped_column(Text)

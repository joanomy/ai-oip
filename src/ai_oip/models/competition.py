"""CompetitionRecord: competitive-landscape assessments at rest."""

import uuid

from sqlalchemy import JSON, Text
from sqlalchemy.orm import Mapped, mapped_column

from ai_oip.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class CompetitionRecord(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """One workflow's competitive assessment (model-knowledge based)."""

    __tablename__ = "competition_assessments"

    workflow_id: Mapped[uuid.UUID]
    workflow_name: Mapped[str]
    saturation: Mapped[str]
    market_gap: Mapped[str | None] = mapped_column(Text)
    #: [{"name": ..., "offering": ..., "positioning": ...}]
    competitors: Mapped[list[dict[str, object]]] = mapped_column(JSON)

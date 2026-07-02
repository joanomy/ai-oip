"""OpportunityScoreRecord: workflow opportunity judgments at rest.

Dimensions are stored as JSON (score + rationale per dimension) with
the deterministic weighted total alongside. workflow_name is
denormalized so the ranking is readable without a join.
"""

import uuid

from sqlalchemy import JSON, Float
from sqlalchemy.orm import Mapped, mapped_column

from ai_oip.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class OpportunityScoreRecord(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """One scored workflow: five judged dimensions plus weighted total."""

    __tablename__ = "opportunity_scores"

    workflow_id: Mapped[uuid.UUID]
    workflow_name: Mapped[str]
    total_score: Mapped[float] = mapped_column(Float)
    #: {dimension: {"score": int, "rationale": str}} for the five dimensions.
    dimensions: Mapped[dict[str, dict[str, object]]] = mapped_column(JSON)

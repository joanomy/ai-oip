"""ProductRecommendationRecord: build/watch/pass recommendations at rest."""

import uuid

from sqlalchemy import JSON, Float, Text
from sqlalchemy.orm import Mapped, mapped_column

from ai_oip.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ProductRecommendationRecord(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """One workflow's product recommendation (scored + competition-assessed)."""

    __tablename__ = "product_recommendations"

    workflow_id: Mapped[uuid.UUID]
    workflow_name: Mapped[str]
    total_score: Mapped[float] = mapped_column(Float)
    recommendation: Mapped[str]
    product_concept: Mapped[str] = mapped_column(Text)
    #: ["step 1", "step 2", ...]
    mvp_scope: Mapped[list[str]] = mapped_column(JSON)
    differentiation: Mapped[str | None] = mapped_column(Text)
    rationale: Mapped[str] = mapped_column(Text)

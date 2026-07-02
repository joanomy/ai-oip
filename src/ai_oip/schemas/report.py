"""Report schemas: the walking skeleton's end-of-pipeline output shape.

Deliberately labeled "skeleton": the Executive Report milestone
replaces the *content* of reporting; this shape exists so the pipeline
has a real, typed terminus from day one.
"""

from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field


class ProblemFinding(BaseModel):
    """One extracted problem, joined with its source attribution."""

    model_config = ConfigDict(frozen=True)

    description: str
    context: str | None = None
    evidence: str | None = None
    source_title: str | None = None
    source_url: str | None = None


class SkeletonReport(BaseModel):
    """The result of one end-to-end discovery run."""

    model_config = ConfigDict(frozen=True)

    query: str
    source: str
    items_collected: int
    findings: list[ProblemFinding]
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

"""Schemas: Pydantic models describing data IN MOTION.

Used for agent inputs/outputs, API request/response bodies, and any
data crossing a module boundary. Never used for database persistence
— see `models/` for that.

Dependency rule: depends only on core.
"""

from ai_oip.schemas.collected_item import CollectedItem
from ai_oip.schemas.problem_extraction import (
    ExtractedProblem,
    ProblemExtractionInput,
    ProblemExtractionOutput,
)
from ai_oip.schemas.report import ProblemFinding, SkeletonReport

__all__ = [
    "CollectedItem",
    "ExtractedProblem",
    "ProblemExtractionInput",
    "ProblemExtractionOutput",
    "ProblemFinding",
    "SkeletonReport",
]

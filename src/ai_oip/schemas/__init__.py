"""Schemas: Pydantic models describing data IN MOTION.

Used for agent inputs/outputs, API request/response bodies, and any
data crossing a module boundary. Never used for database persistence
— see `models/` for that.

Dependency rule: depends only on core.
"""

from ai_oip.schemas.collected_item import CollectedItem
from ai_oip.schemas.opportunity_scoring import (
    DimensionScore,
    OpportunityReport,
    OpportunityScoringInput,
    OpportunityScoringOutput,
    RankedOpportunity,
    WorkflowDetail,
    WorkflowScore,
)
from ai_oip.schemas.problem_extraction import (
    ExtractedProblem,
    ProblemExtractionInput,
    ProblemExtractionOutput,
)
from ai_oip.schemas.report import ProblemFinding, SkeletonReport
from ai_oip.schemas.workflow_discovery import (
    DiscoveredWorkflow,
    ProblemDetail,
    WorkflowDiscoveryInput,
    WorkflowDiscoveryOutput,
    WorkflowReport,
    WorkflowSummary,
)

__all__ = [
    "CollectedItem",
    "DimensionScore",
    "DiscoveredWorkflow",
    "ExtractedProblem",
    "OpportunityReport",
    "OpportunityScoringInput",
    "OpportunityScoringOutput",
    "ProblemDetail",
    "ProblemExtractionInput",
    "ProblemExtractionOutput",
    "ProblemFinding",
    "RankedOpportunity",
    "SkeletonReport",
    "WorkflowDetail",
    "WorkflowDiscoveryInput",
    "WorkflowDiscoveryOutput",
    "WorkflowReport",
    "WorkflowScore",
    "WorkflowSummary",
]

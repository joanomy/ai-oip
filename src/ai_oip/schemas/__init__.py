"""Schemas: Pydantic models describing data IN MOTION.

Used for agent inputs/outputs, API request/response bodies, and any
data crossing a module boundary. Never used for database persistence
— see `models/` for that.

Dependency rule: depends only on core.
"""

from ai_oip.schemas.collected_item import CollectedItem
from ai_oip.schemas.competition_research import (
    CompetitionReport,
    CompetitionResearchInput,
    CompetitionResearchOutput,
    CompetitionSummary,
    Competitor,
    OpportunityDetail,
    ResearchTarget,
    WorkflowCompetition,
)
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
from ai_oip.schemas.product_recommendation import (
    CompetitionDetail,
    ProductPlan,
    ProductRecommendationInput,
    ProductRecommendationOutput,
    RecommendationReport,
    RecommendationSummary,
    RecommendationTarget,
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
    "CompetitionDetail",
    "CompetitionReport",
    "CompetitionResearchInput",
    "CompetitionResearchOutput",
    "CompetitionSummary",
    "Competitor",
    "DimensionScore",
    "DiscoveredWorkflow",
    "ExtractedProblem",
    "OpportunityDetail",
    "OpportunityReport",
    "OpportunityScoringInput",
    "OpportunityScoringOutput",
    "ProblemDetail",
    "ProblemExtractionInput",
    "ProblemExtractionOutput",
    "ProblemFinding",
    "ProductPlan",
    "ProductRecommendationInput",
    "ProductRecommendationOutput",
    "RankedOpportunity",
    "RecommendationReport",
    "RecommendationSummary",
    "RecommendationTarget",
    "ResearchTarget",
    "SkeletonReport",
    "WorkflowCompetition",
    "WorkflowDetail",
    "WorkflowDiscoveryInput",
    "WorkflowDiscoveryOutput",
    "WorkflowReport",
    "WorkflowScore",
    "WorkflowSummary",
]

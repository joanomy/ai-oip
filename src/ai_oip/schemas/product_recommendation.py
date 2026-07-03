"""I/O schemas for the Product Recommendation agent, plus the stored-
assessment read shape and the report."""

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from ai_oip.schemas.competition_research import Competitor
from ai_oip.schemas.opportunity_scoring import WorkflowDetail


class CompetitionDetail(BaseModel):
    """A stored competition assessment, as data in motion (repository read result)."""

    model_config = ConfigDict(frozen=True)

    workflow_id: UUID
    saturation: Literal["low", "medium", "high"]
    market_gap: str | None
    competitors: list[Competitor]


class RecommendationTarget(BaseModel):
    """One researched opportunity to recommend on."""

    model_config = ConfigDict(frozen=True)

    workflow: WorkflowDetail
    total_score: float
    competition: CompetitionDetail


class ProductRecommendationInput(BaseModel):
    """A batch of researched opportunities to recommend on."""

    model_config = ConfigDict(frozen=True)

    targets: list[RecommendationTarget]


class ProductPlan(BaseModel):
    """The agent's recommendation for one workflow."""

    model_config = ConfigDict(frozen=True)

    workflow_index: int = Field(ge=1)
    recommendation: Literal["build", "watch", "pass"]
    product_concept: str
    mvp_scope: list[str] = Field(default_factory=list)
    differentiation: str | None = None
    rationale: str


class ProductRecommendationOutput(BaseModel):
    """The agent's full recommendation result."""

    model_config = ConfigDict(frozen=True)

    plans: list[ProductPlan]


class RecommendationSummary(BaseModel):
    """One recommended workflow (report shape)."""

    model_config = ConfigDict(frozen=True)

    workflow_name: str
    total_score: float
    saturation: Literal["low", "medium", "high"]
    recommendation: Literal["build", "watch", "pass"]
    product_concept: str
    mvp_scope: list[str]
    differentiation: str | None
    rationale: str


class RecommendationReport(BaseModel):
    """The result of one product-recommendation run."""

    model_config = ConfigDict(frozen=True)

    targets_analyzed: int
    recommendations: list[RecommendationSummary]

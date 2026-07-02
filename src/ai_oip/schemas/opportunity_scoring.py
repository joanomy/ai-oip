"""I/O schemas for the Opportunity Scoring agent, plus the stored-workflow
read shape and the ranked report.

The dimensions are a fixed, typed set (not a free dict): the model
must score exactly these five, and a missing or misspelled dimension
fails validation at the guardrail instead of skewing totals silently.
"""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class WorkflowDetail(BaseModel):
    """A stored workflow, as data in motion (repository read result)."""

    model_config = ConfigDict(frozen=True)

    id: UUID
    name: str
    description: str
    steps: list[str]
    actors: list[str]
    problems_linked: int


class OpportunityScoringInput(BaseModel):
    """A batch of stored workflows to score."""

    model_config = ConfigDict(frozen=True)

    workflows: list[WorkflowDetail]


class DimensionScore(BaseModel):
    """One judged dimension: integer score plus grounding rationale."""

    model_config = ConfigDict(frozen=True)

    score: int = Field(ge=1, le=10)
    rationale: str


class WorkflowScore(BaseModel):
    """The agent's five-dimension judgment for one workflow."""

    model_config = ConfigDict(frozen=True)

    workflow_index: int = Field(ge=1)
    pain_intensity: DimensionScore
    automation_feasibility: DimensionScore
    frequency: DimensionScore
    market_breadth: DimensionScore
    willingness_to_pay: DimensionScore


class OpportunityScoringOutput(BaseModel):
    """The agent's full scoring result."""

    model_config = ConfigDict(frozen=True)

    scores: list[WorkflowScore]


class RankedOpportunity(BaseModel):
    """One workflow with its deterministic weighted total (report shape)."""

    model_config = ConfigDict(frozen=True)

    workflow_name: str
    total_score: float = Field(description="Weighted total on a 10-100 scale.")
    score: WorkflowScore


class OpportunityReport(BaseModel):
    """The result of one scoring run, ranked best-first."""

    model_config = ConfigDict(frozen=True)

    workflows_scored: int
    opportunities: list[RankedOpportunity]

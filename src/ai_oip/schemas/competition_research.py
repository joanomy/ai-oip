"""I/O schemas for the Competition Research agent, plus the stored-score
read shape and the report."""

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from ai_oip.schemas.opportunity_scoring import WorkflowDetail


class OpportunityDetail(BaseModel):
    """A stored opportunity score, as data in motion (repository read result)."""

    model_config = ConfigDict(frozen=True)

    id: UUID
    workflow_id: UUID
    workflow_name: str
    total_score: float


class ResearchTarget(BaseModel):
    """One workflow to research, with its opportunity score for context."""

    model_config = ConfigDict(frozen=True)

    workflow: WorkflowDetail
    total_score: float


class CompetitionResearchInput(BaseModel):
    """A batch of top-ranked opportunities to research."""

    model_config = ConfigDict(frozen=True)

    targets: list[ResearchTarget]


class Competitor(BaseModel):
    """One known competitor addressing a workflow."""

    model_config = ConfigDict(frozen=True)

    name: str
    offering: str
    positioning: str | None = None


class WorkflowCompetition(BaseModel):
    """The agent's competitive assessment for one workflow."""

    model_config = ConfigDict(frozen=True)

    workflow_index: int = Field(ge=1)
    competitors: list[Competitor] = Field(default_factory=list)
    market_gap: str | None = None
    saturation: Literal["low", "medium", "high"]


class CompetitionResearchOutput(BaseModel):
    """The agent's full research result."""

    model_config = ConfigDict(frozen=True)

    assessments: list[WorkflowCompetition]


class CompetitionSummary(BaseModel):
    """One assessed workflow (report shape)."""

    model_config = ConfigDict(frozen=True)

    workflow_name: str
    total_score: float
    saturation: Literal["low", "medium", "high"]
    market_gap: str | None
    competitors: list[Competitor]
    #: Web sources consulted during the run that produced this
    #: assessment (R1/ADR-0018) — batch-level provenance extracted by
    #: the provider from search-tool results, never model-authored
    #: text. Empty when the run was ungrounded (pre-R1 behavior).
    sources: tuple[str, ...] = ()


class CompetitionReport(BaseModel):
    """The result of one competition-research run."""

    model_config = ConfigDict(frozen=True)

    targets_analyzed: int
    assessments: list[CompetitionSummary]
    #: True if this run's assessments were grounded in live web search
    #: (R1) rather than model knowledge alone (v1, ADR-0013). Drives the
    #: report banner — grounded runs get a "grounded as of" note instead
    #: of the knowledge-lag disclaimer.
    grounded: bool = False

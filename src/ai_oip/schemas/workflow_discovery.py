"""I/O schemas for the Workflow Discovery agent, plus the stored-problem
shape repositories hand upward (the ORM never crosses that boundary)."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ProblemDetail(BaseModel):
    """A stored problem, as data in motion (repository read result)."""

    model_config = ConfigDict(frozen=True)

    id: UUID
    description: str
    context: str | None = None
    evidence: str | None = None
    source: str


class WorkflowDiscoveryInput(BaseModel):
    """A batch of stored problems to discover workflows behind."""

    model_config = ConfigDict(frozen=True)

    problems: list[ProblemDetail]


class DiscoveredWorkflow(BaseModel):
    """One recurring business workflow the agent identified."""

    model_config = ConfigDict(frozen=True)

    name: str
    description: str
    steps: list[str] = Field(default_factory=list)
    actors: list[str] = Field(default_factory=list)
    problem_indexes: list[int] = Field(
        default_factory=list,
        description="1-based indexes of the input problems this workflow underlies.",
    )


class WorkflowDiscoveryOutput(BaseModel):
    """The agent's full discovery result. Empty list = nothing recurring."""

    model_config = ConfigDict(frozen=True)

    workflows: list[DiscoveredWorkflow]


class WorkflowSummary(BaseModel):
    """One discovered workflow with resolved problem attribution (report shape)."""

    model_config = ConfigDict(frozen=True)

    name: str
    description: str
    steps: list[str]
    actors: list[str]
    problems_linked: int


class WorkflowReport(BaseModel):
    """The result of one workflow-discovery run."""

    model_config = ConfigDict(frozen=True)

    problems_analyzed: int
    workflows: list[WorkflowSummary]

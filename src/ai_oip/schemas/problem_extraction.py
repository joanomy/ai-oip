"""I/O schemas for the Problem Extraction agent."""

from pydantic import BaseModel, ConfigDict, Field

from ai_oip.schemas.collected_item import CollectedItem


class ProblemExtractionInput(BaseModel):
    """A batch of collected items to extract problems from."""

    model_config = ConfigDict(frozen=True)

    items: list[CollectedItem]


class ExtractedProblem(BaseModel):
    """One concrete problem a person described in the collected signal."""

    model_config = ConfigDict(frozen=True)

    description: str
    context: str | None = None
    evidence: str | None = None
    source_index: int | None = Field(
        default=None,
        ge=1,
        description="1-based index of the input item this problem came from.",
    )


class ProblemExtractionOutput(BaseModel):
    """The agent's full extraction result. Empty list = no problems found."""

    model_config = ConfigDict(frozen=True)

    problems: list[ExtractedProblem]

"""Repository for competition assessments — schemas in, ORM stays inside."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from ai_oip.models import CompetitionRecord
from ai_oip.repositories.sqlalchemy_repository import SQLAlchemyRepository
from ai_oip.schemas import WorkflowCompetition


class CompetitionRepository(SQLAlchemyRepository[CompetitionRecord]):
    """CRUD plus domain writes for competition assessments."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, CompetitionRecord)

    async def add_assessment(
        self,
        assessment: WorkflowCompetition,
        *,
        workflow_id: UUID,
        workflow_name: str,
    ) -> None:
        """Persist one workflow's competitive assessment."""
        record = CompetitionRecord(
            workflow_id=workflow_id,
            workflow_name=workflow_name,
            saturation=assessment.saturation,
            market_gap=assessment.market_gap,
            competitors=[
                {
                    "name": competitor.name,
                    "offering": competitor.offering,
                    "positioning": competitor.positioning,
                }
                for competitor in assessment.competitors
            ],
        )
        await self.save(record)

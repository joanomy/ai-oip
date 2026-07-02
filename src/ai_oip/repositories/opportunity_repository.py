"""Repository for opportunity scores — schemas in, ORM stays inside."""

from sqlalchemy.ext.asyncio import AsyncSession

from ai_oip.models import OpportunityScoreRecord
from ai_oip.repositories.sqlalchemy_repository import SQLAlchemyRepository
from ai_oip.schemas import WorkflowDetail, WorkflowScore


class OpportunityRepository(SQLAlchemyRepository[OpportunityScoreRecord]):
    """CRUD plus domain writes for opportunity scores."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, OpportunityScoreRecord)

    async def add_score(
        self,
        *,
        workflow: WorkflowDetail,
        score: WorkflowScore,
        total_score: float,
    ) -> None:
        """Persist one workflow's judged dimensions and weighted total."""
        record = OpportunityScoreRecord(
            workflow_id=workflow.id,
            workflow_name=workflow.name,
            total_score=total_score,
            dimensions={
                dimension: {
                    "score": getattr(score, dimension).score,
                    "rationale": getattr(score, dimension).rationale,
                }
                for dimension in (
                    "pain_intensity",
                    "automation_feasibility",
                    "frequency",
                    "market_breadth",
                    "willingness_to_pay",
                )
            },
        )
        await self.save(record)

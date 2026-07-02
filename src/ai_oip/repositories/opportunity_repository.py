"""Repository for opportunity scores — schemas in, schemas out."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ai_oip.core.exceptions import RepositoryError
from ai_oip.models import OpportunityScoreRecord
from ai_oip.repositories.sqlalchemy_repository import SQLAlchemyRepository
from ai_oip.schemas import OpportunityDetail, WorkflowDetail, WorkflowScore


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

    async def list_top(self, *, limit: int = 5) -> list[OpportunityDetail]:
        """Highest-scored opportunities, as data in motion (best first)."""
        try:
            result = await self._session.execute(
                select(OpportunityScoreRecord)
                .order_by(OpportunityScoreRecord.total_score.desc())
                .limit(limit)
            )
            records = result.scalars().all()
        except Exception as exc:
            raise RepositoryError(f"Failed to list top opportunities: {exc}") from exc
        return [
            OpportunityDetail(
                id=record.id,
                workflow_id=record.workflow_id,
                workflow_name=record.workflow_name,
                total_score=record.total_score,
            )
            for record in records
        ]

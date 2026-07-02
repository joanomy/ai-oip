"""Repository for discovered workflows — schemas in, schemas out."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ai_oip.core.exceptions import RepositoryError
from ai_oip.models import WorkflowRecord
from ai_oip.repositories.sqlalchemy_repository import SQLAlchemyRepository
from ai_oip.schemas import DiscoveredWorkflow, WorkflowDetail


class WorkflowRepository(SQLAlchemyRepository[WorkflowRecord]):
    """CRUD plus domain writes for workflows."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, WorkflowRecord)

    async def add_discovered(
        self, workflow: DiscoveredWorkflow, *, problem_ids: list[UUID]
    ) -> None:
        """Persist one discovered workflow linked to its problems."""
        record = WorkflowRecord(
            name=workflow.name,
            description=workflow.description,
            steps=list(workflow.steps),
            actors=list(workflow.actors),
            problem_ids=[str(problem_id) for problem_id in problem_ids],
        )
        await self.save(record)

    async def list_details(self, *, limit: int = 50) -> list[WorkflowDetail]:
        """Most recent workflows, as data in motion (newest first)."""
        try:
            result = await self._session.execute(
                select(WorkflowRecord).order_by(WorkflowRecord.created_at.desc()).limit(limit)
            )
            records = result.scalars().all()
        except Exception as exc:
            raise RepositoryError(f"Failed to list workflow details: {exc}") from exc
        return [
            WorkflowDetail(
                id=record.id,
                name=record.name,
                description=record.description,
                steps=record.steps,
                actors=record.actors,
                problems_linked=len(record.problem_ids),
            )
            for record in records
        ]

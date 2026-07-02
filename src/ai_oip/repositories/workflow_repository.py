"""Repository for discovered workflows — schemas in, ORM stays inside."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from ai_oip.models import WorkflowRecord
from ai_oip.repositories.sqlalchemy_repository import SQLAlchemyRepository
from ai_oip.schemas import DiscoveredWorkflow


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

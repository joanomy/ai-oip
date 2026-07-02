"""Repository for extracted problems.

Accepts *schemas* and constructs ORM records internally — the ORM
never crosses this boundary upward. This is what lets services stay
inside the "only repositories access the database layer" contract
while still persisting things: they hand over data in motion, the
repository owns data at rest.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ai_oip.core.exceptions import RepositoryError
from ai_oip.models import ProblemRecord
from ai_oip.repositories.sqlalchemy_repository import SQLAlchemyRepository
from ai_oip.schemas import CollectedItem, ExtractedProblem, ProblemDetail


class ProblemRepository(SQLAlchemyRepository[ProblemRecord]):
    """CRUD plus domain writes for problems."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, ProblemRecord)

    async def add_extracted(
        self,
        problem: ExtractedProblem,
        *,
        source_item: CollectedItem | None,
        collector_name: str,
    ) -> None:
        """Persist one extracted problem with its source attribution.

        `source_item` is None when the agent's source_index didn't
        resolve to a collected item — the problem is still stored,
        attributed to the collector rather than a specific item.
        """
        record = ProblemRecord(
            source=source_item.source if source_item is not None else collector_name,
            source_external_id=source_item.external_id if source_item is not None else None,
            source_title=source_item.title if source_item is not None else None,
            source_url=source_item.url if source_item is not None else None,
            description=problem.description,
            context=problem.context,
            evidence=problem.evidence,
        )
        await self.save(record)

    async def list_details(self, *, limit: int = 50) -> list[ProblemDetail]:
        """Most recent problems, as data in motion (newest first).

        Returns schemas, not ORM records — the read-path counterpart of
        `add_extracted`, keeping the ORM inside the repository.
        """
        try:
            result = await self._session.execute(
                select(ProblemRecord).order_by(ProblemRecord.created_at.desc()).limit(limit)
            )
            records = result.scalars().all()
        except Exception as exc:
            raise RepositoryError(f"Failed to list problem details: {exc}") from exc
        return [
            ProblemDetail(
                id=record.id,
                description=record.description,
                context=record.context,
                evidence=record.evidence,
                source=record.source,
            )
            for record in records
        ]

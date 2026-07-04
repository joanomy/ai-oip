"""Repository for competition assessments — schemas in, schemas out."""

from collections.abc import Sequence
from typing import Literal, cast
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ai_oip.core.exceptions import RepositoryError
from ai_oip.models import CompetitionRecord
from ai_oip.repositories.sqlalchemy_repository import SQLAlchemyRepository
from ai_oip.schemas import CompetitionDetail, Competitor, WorkflowCompetition


class CompetitionRepository(SQLAlchemyRepository[CompetitionRecord]):
    """CRUD plus domain writes for competition assessments."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, CompetitionRecord)

    async def get_latest_by_workflow(self, workflow_id: UUID) -> CompetitionDetail | None:
        """Most recent assessment for a workflow, or None if unresearched.

        A workflow may be re-researched (stale assessment refreshed); the
        freshest assessment is the one worth trusting given the honesty/
        knowledge-lag concerns baked into the research prompt (ADR-0013).
        """
        try:
            result = await self._session.execute(
                select(CompetitionRecord)
                .where(CompetitionRecord.workflow_id == workflow_id)
                .order_by(CompetitionRecord.created_at.desc())
                .limit(1)
            )
            record = result.scalars().first()
        except Exception as exc:
            raise RepositoryError(f"Failed to fetch competition assessment: {exc}") from exc
        if record is None:
            return None
        return CompetitionDetail(
            workflow_id=record.workflow_id,
            saturation=cast(Literal["low", "medium", "high"], record.saturation),
            market_gap=record.market_gap,
            competitors=[
                Competitor(
                    name=cast(str, competitor["name"]),
                    offering=cast(str, competitor["offering"]),
                    positioning=cast("str | None", competitor["positioning"]),
                )
                for competitor in record.competitors
            ],
        )

    async def add_assessment(
        self,
        assessment: WorkflowCompetition,
        *,
        workflow_id: UUID,
        workflow_name: str,
        sources: Sequence[str] | None = None,
    ) -> None:
        """Persist one workflow's competitive assessment.

        `sources` is None for an ungrounded run (v1, ADR-0013) and a
        (possibly empty) list for a grounded run (R1, ADR-0018) — the
        column stays nullable so "not grounded" and "grounded, found
        nothing" remain distinguishable in stored data.
        """
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
            sources=list(sources) if sources is not None else None,
        )
        await self.save(record)

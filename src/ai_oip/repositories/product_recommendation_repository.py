"""Repository for product recommendations — schemas in, ORM stays inside."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from ai_oip.models import ProductRecommendationRecord
from ai_oip.repositories.sqlalchemy_repository import SQLAlchemyRepository
from ai_oip.schemas import ProductPlan


class ProductRecommendationRepository(SQLAlchemyRepository[ProductRecommendationRecord]):
    """CRUD plus domain writes for product recommendations."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, ProductRecommendationRecord)

    async def add_recommendation(
        self,
        plan: ProductPlan,
        *,
        workflow_id: UUID,
        workflow_name: str,
        total_score: float,
    ) -> None:
        """Persist one workflow's product recommendation."""
        record = ProductRecommendationRecord(
            workflow_id=workflow_id,
            workflow_name=workflow_name,
            total_score=total_score,
            recommendation=plan.recommendation,
            product_concept=plan.product_concept,
            mvp_scope=list(plan.mvp_scope),
            differentiation=plan.differentiation,
            rationale=plan.rationale,
        )
        await self.save(record)

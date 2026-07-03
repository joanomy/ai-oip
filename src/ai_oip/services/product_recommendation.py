"""Product recommendation orchestration: researched opportunities -> plans.

Second three-store read (scores + workflow details + competition
assessments) in the pipeline. A scored workflow that hasn't been
researched yet (M11 competition research not run for it) is skipped,
not failed — a recommendation without a competitive landscape is a
guess, not a judgment (ADR-0016). This is the join-dedup pattern's
second occurrence (competition research was the first, ADR-0013); a
shared read-helper is deferred until a third occurrence (ADR-0014).
"""

from ai_oip.agents import log_agent_run
from ai_oip.agents.product_recommendation import ProductRecommendationAgent
from ai_oip.repositories import (
    CompetitionRepository,
    OpportunityRepository,
    ProductRecommendationRepository,
    WorkflowRepository,
)
from ai_oip.schemas import (
    ProductRecommendationInput,
    RecommendationReport,
    RecommendationSummary,
    RecommendationTarget,
)


class ProductRecommendationService:
    """Read researched opportunities, recommend, persist, report."""

    def __init__(
        self,
        *,
        agent: ProductRecommendationAgent,
        opportunity_repository: OpportunityRepository,
        workflow_repository: WorkflowRepository,
        competition_repository: CompetitionRepository,
        recommendation_repository: ProductRecommendationRepository,
    ) -> None:
        self._agent = agent
        self._opportunities = opportunity_repository
        self._workflows = workflow_repository
        self._competition = competition_repository
        self._recommendations = recommendation_repository

    async def recommend(self, *, limit: int = 5) -> RecommendationReport:
        """Run one recommendation pass over researched opportunities."""
        targets = await self._build_targets(limit)

        summaries: list[RecommendationSummary] = []
        if targets:
            with log_agent_run(self._agent.name):
                output = await self._agent.run(ProductRecommendationInput(targets=targets))

            for plan in output.plans:
                if not 1 <= plan.workflow_index <= len(targets):
                    continue  # a plan with no target is meaningless
                target = targets[plan.workflow_index - 1]
                await self._recommendations.add_recommendation(
                    plan,
                    workflow_id=target.workflow.id,
                    workflow_name=target.workflow.name,
                    total_score=target.total_score,
                )
                summaries.append(
                    RecommendationSummary(
                        workflow_name=target.workflow.name,
                        total_score=target.total_score,
                        saturation=target.competition.saturation,
                        recommendation=plan.recommendation,
                        product_concept=plan.product_concept,
                        mvp_scope=plan.mvp_scope,
                        differentiation=plan.differentiation,
                        rationale=plan.rationale,
                    )
                )

        return RecommendationReport(targets_analyzed=len(targets), recommendations=summaries)

    async def _build_targets(self, limit: int) -> list[RecommendationTarget]:
        """Top scores joined with workflow details and their latest
        competition assessment, deduped by workflow.

        Over-fetches at 4x `limit`: on top of the re-scored-workflow
        dedupe that competition research also faces, a target here is
        additionally dropped when it hasn't been researched yet.
        """
        top_scores = await self._opportunities.list_top(limit=limit * 4)

        targets: list[RecommendationTarget] = []
        seen_workflows: set[str] = set()
        for score in top_scores:
            if len(targets) >= limit:
                break
            key = str(score.workflow_id)
            if key in seen_workflows:
                continue  # already targeting this workflow at a better score
            workflow = await self._workflows.get_detail(score.workflow_id)
            if workflow is None:
                continue  # dangling score — workflow no longer exists
            competition = await self._competition.get_latest_by_workflow(score.workflow_id)
            if competition is None:
                continue  # not yet researched — nothing to ground a recommendation in
            seen_workflows.add(key)
            targets.append(
                RecommendationTarget(
                    workflow=workflow, total_score=score.total_score, competition=competition
                )
            )
        return targets

"""Competition research orchestration: top opportunities -> assessments.

First service reading across two stores: the top-ranked scores plus
their workflow details. Re-scored workflows are deduplicated (best
score wins) so an opportunity isn't researched twice in one run.
"""

from ai_oip.agents import log_agent_run
from ai_oip.agents.competition_research import CompetitionResearchAgent
from ai_oip.repositories import (
    CompetitionRepository,
    OpportunityRepository,
    WorkflowRepository,
)
from ai_oip.schemas import (
    CompetitionReport,
    CompetitionResearchInput,
    CompetitionSummary,
    ResearchTarget,
)


class CompetitionResearchService:
    """Read top opportunities, assess their landscapes, persist, report."""

    def __init__(
        self,
        *,
        agent: CompetitionResearchAgent,
        opportunity_repository: OpportunityRepository,
        workflow_repository: WorkflowRepository,
        competition_repository: CompetitionRepository,
    ) -> None:
        self._agent = agent
        self._opportunities = opportunity_repository
        self._workflows = workflow_repository
        self._competition = competition_repository

    async def research(self, *, limit: int = 5) -> CompetitionReport:
        """Run one research pass over the top-scored workflows."""
        targets = await self._build_targets(limit)

        summaries: list[CompetitionSummary] = []
        if targets:
            with log_agent_run(self._agent.name):
                output, response = await self._agent.run_detailed(
                    CompetitionResearchInput(targets=targets)
                )
            # Batch-level provenance: one completion covers every target
            # in this run, so the same source list attaches to each
            # persisted assessment (R1/ADR-0018) — never per-target,
            # since the model cannot attribute sources per competitor.
            sources = response.sources if self._agent.grounded else None

            for assessment in output.assessments:
                if not 1 <= assessment.workflow_index <= len(targets):
                    continue  # an assessment with no target is meaningless
                target = targets[assessment.workflow_index - 1]
                await self._competition.add_assessment(
                    assessment,
                    workflow_id=target.workflow.id,
                    workflow_name=target.workflow.name,
                    sources=sources,
                )
                summaries.append(
                    CompetitionSummary(
                        workflow_name=target.workflow.name,
                        total_score=target.total_score,
                        saturation=assessment.saturation,
                        market_gap=assessment.market_gap,
                        competitors=assessment.competitors,
                        sources=sources or (),
                    )
                )

        return CompetitionReport(
            targets_analyzed=len(targets),
            assessments=summaries,
            grounded=self._agent.grounded,
        )

    async def _build_targets(self, limit: int) -> list[ResearchTarget]:
        """Top scores joined with workflow details, deduped by workflow.

        `list_top` over-fetches so that duplicates (re-scored workflows)
        and dangling workflow_ids still leave up to `limit` targets.
        """
        top_scores = await self._opportunities.list_top(limit=limit * 3)

        targets: list[ResearchTarget] = []
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
            seen_workflows.add(key)
            targets.append(ResearchTarget(workflow=workflow, total_score=score.total_score))
        return targets

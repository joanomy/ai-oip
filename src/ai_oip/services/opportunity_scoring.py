"""Opportunity scoring orchestration: the LLM judges, this code computes.

The weighted total is deterministic arithmetic over the agent's
per-dimension scores. Weights are a constructor argument (a business
rule owned by composition, not hardcoded in a prompt and not buried
here) — `DEFAULT_WEIGHTS` is the CEO-approved starting rubric.
"""

from ai_oip.agents import log_agent_run
from ai_oip.agents.opportunity_scoring import OpportunityScoringAgent
from ai_oip.repositories import OpportunityRepository, WorkflowRepository
from ai_oip.schemas import (
    OpportunityReport,
    OpportunityScoringInput,
    RankedOpportunity,
    WorkflowScore,
)

#: Approved starting rubric (ADR-0012). Sum of weights must be 1.0.
DEFAULT_WEIGHTS: dict[str, float] = {
    "pain_intensity": 0.25,
    "automation_feasibility": 0.25,
    "frequency": 0.20,
    "market_breadth": 0.20,
    "willingness_to_pay": 0.10,
}


def weighted_total(score: WorkflowScore, weights: dict[str, float]) -> float:
    """Deterministic weighted total on a 10-100 scale."""
    raw = sum(
        float(getattr(score, dimension).score) * weight for dimension, weight in weights.items()
    )
    return round(raw * 10, 1)


class OpportunityScoringService:
    """Read stored workflows, judge them, compute totals, persist, rank."""

    def __init__(
        self,
        *,
        agent: OpportunityScoringAgent,
        workflow_repository: WorkflowRepository,
        opportunity_repository: OpportunityRepository,
        weights: dict[str, float] | None = None,
    ) -> None:
        self._agent = agent
        self._workflows = workflow_repository
        self._opportunities = opportunity_repository
        self._weights = weights if weights is not None else DEFAULT_WEIGHTS

    async def score(self, *, limit: int = 20) -> OpportunityReport:
        """Run one scoring pass over the most recent stored workflows."""
        workflows = await self._workflows.list_details(limit=limit)

        ranked: list[RankedOpportunity] = []
        if workflows:
            with log_agent_run(self._agent.name):
                output = await self._agent.run(OpportunityScoringInput(workflows=workflows))

            for score in output.scores:
                if not 1 <= score.workflow_index <= len(workflows):
                    continue  # a judgment with no workflow to attach to is meaningless
                workflow = workflows[score.workflow_index - 1]
                total = weighted_total(score, self._weights)
                await self._opportunities.add_score(
                    workflow=workflow, score=score, total_score=total
                )
                ranked.append(
                    RankedOpportunity(workflow_name=workflow.name, total_score=total, score=score)
                )

        ranked.sort(key=lambda opportunity: opportunity.total_score, reverse=True)
        return OpportunityReport(workflows_scored=len(ranked), opportunities=ranked)

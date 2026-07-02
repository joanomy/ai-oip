"""Workflow discovery orchestration: stored problems -> workflows at rest.

Second service, same shape as problem discovery: repositories arrive
bound to a unit of work, everything crossing the boundary is a schema.
"""

from uuid import UUID

from ai_oip.agents import log_agent_run
from ai_oip.agents.workflow_discovery import WorkflowDiscoveryAgent
from ai_oip.repositories import ProblemRepository, WorkflowRepository
from ai_oip.schemas import (
    ProblemDetail,
    WorkflowDiscoveryInput,
    WorkflowReport,
    WorkflowSummary,
)


class WorkflowDiscoveryService:
    """Read stored problems, discover workflows, persist them, report."""

    def __init__(
        self,
        *,
        agent: WorkflowDiscoveryAgent,
        problem_repository: ProblemRepository,
        workflow_repository: WorkflowRepository,
    ) -> None:
        self._agent = agent
        self._problems = problem_repository
        self._workflows = workflow_repository

    async def discover(self, *, limit: int = 50) -> WorkflowReport:
        """Run one discovery pass over the most recent stored problems."""
        problems = await self._problems.list_details(limit=limit)

        summaries: list[WorkflowSummary] = []
        if problems:
            with log_agent_run(self._agent.name):
                output = await self._agent.run(WorkflowDiscoveryInput(problems=problems))

            for workflow in output.workflows:
                problem_ids = self._resolve_problem_ids(workflow.problem_indexes, problems)
                await self._workflows.add_discovered(workflow, problem_ids=problem_ids)
                summaries.append(
                    WorkflowSummary(
                        name=workflow.name,
                        description=workflow.description,
                        steps=workflow.steps,
                        actors=workflow.actors,
                        problems_linked=len(problem_ids),
                    )
                )

        return WorkflowReport(problems_analyzed=len(problems), workflows=summaries)

    @staticmethod
    def _resolve_problem_ids(indexes: list[int], problems: list[ProblemDetail]) -> list[UUID]:
        """Map 1-based indexes to problem ids; invalid indexes are dropped.

        Same degradation stance as problem extraction: a slightly wrong
        index costs one linkage, never the discovery.
        """
        return [problems[index - 1].id for index in indexes if 1 <= index <= len(problems)]

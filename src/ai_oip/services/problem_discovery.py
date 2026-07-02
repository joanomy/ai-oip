"""Problem discovery: the walking skeleton's orchestration.

The first service — and the demonstration of the layer contract in
practice: it composes a collector, an agent, and a repository, but it
imports no ORM and holds no session. The repository instance arrives
bound to a unit of work created by the composition root (`runtime/`);
persistence happens through schema-accepting repository methods.
"""

from ai_oip.agents import log_agent_run
from ai_oip.agents.problem_extraction import ProblemExtractionAgent
from ai_oip.collectors import BaseCollector
from ai_oip.repositories import ProblemRepository
from ai_oip.schemas import (
    CollectedItem,
    ProblemExtractionInput,
    ProblemFinding,
    SkeletonReport,
)


class ProblemDiscoveryService:
    """Collect raw signal, extract problems, persist them, report."""

    def __init__(
        self,
        *,
        collector: BaseCollector,
        agent: ProblemExtractionAgent,
        repository: ProblemRepository,
    ) -> None:
        self._collector = collector
        self._agent = agent
        self._repository = repository

    async def discover(self, query: str, *, limit: int = 20) -> SkeletonReport:
        """Run one end-to-end discovery pass for `query`."""
        items = await self._collector.collect(query, limit=limit)

        findings: list[ProblemFinding] = []
        if items:
            with log_agent_run(self._agent.name):
                output = await self._agent.run(ProblemExtractionInput(items=items))

            for problem in output.problems:
                source_item = self._resolve_source(problem.source_index, items)
                await self._repository.add_extracted(
                    problem,
                    source_item=source_item,
                    collector_name=self._collector.name,
                )
                findings.append(
                    ProblemFinding(
                        description=problem.description,
                        context=problem.context,
                        evidence=problem.evidence,
                        source_title=source_item.title if source_item else None,
                        source_url=source_item.url if source_item else None,
                    )
                )

        return SkeletonReport(
            query=query,
            source=self._collector.name,
            items_collected=len(items),
            findings=findings,
        )

    @staticmethod
    def _resolve_source(
        source_index: int | None, items: list[CollectedItem]
    ) -> CollectedItem | None:
        """Map the agent's 1-based source_index back to a collected item.

        An out-of-range or missing index degrades to None (problem is
        stored without item-level attribution) rather than failing the
        run — a slightly-off index is not worth losing the extraction.
        """
        if source_index is None or not 1 <= source_index <= len(items):
            return None
        return items[source_index - 1]

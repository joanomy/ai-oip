"""Collector interface: external raw signal in, normalized CollectedItems out.

Collectors never persist anything (services own that) and never parse
meaning out of the data (agents own that) — they fetch and normalize,
nothing more. One collector per source, registered/composed by the
caller like agents and providers are.

Contract: `collect` either returns items or raises `CollectorError` —
transport/SDK exceptions never escape a collector (same rule as
`LLMProvider.complete`).
"""

from abc import ABC, abstractmethod

from ai_oip.schemas import CollectedItem


class BaseCollector(ABC):
    """Abstract base class all collectors implement."""

    #: Collector/source name; stamped into every CollectedItem.source.
    name: str

    @abstractmethod
    async def collect(self, query: str, *, limit: int = 20) -> list[CollectedItem]:
        """Fetch up to `limit` items matching `query` from the source.

        Raises:
            CollectorError: on any transport, API, or payload failure.
        """
        raise NotImplementedError  # pragma: no cover

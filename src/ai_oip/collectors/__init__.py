"""Collectors: external data ingestion (APIs, scrapers, feeds).

Responsible for pulling raw data from the outside world and converting
it into typed schemas (`CollectedItem`). Collectors do not persist data
(services own that) and do not interpret it (agents own that).

Dependency rule: depends on schemas, core.
"""

from ai_oip.collectors.base import BaseCollector
from ai_oip.collectors.hackernews import HackerNewsCollector

__all__ = ["BaseCollector", "HackerNewsCollector"]

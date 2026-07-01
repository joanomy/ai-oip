"""Collectors: external data ingestion (APIs, scrapers, feeds).

Responsible for pulling raw data from the outside world and converting
it into typed schemas. Collectors do not persist data themselves.

Dependency rule: depends on schemas, core.
"""

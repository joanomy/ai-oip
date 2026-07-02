"""Services: business logic that coordinates repositories, agents,
and collectors to accomplish a unit of work.

This is the layer allowed to know about both persistence (repositories)
and AI execution (agents) — neither of those layers know about each
other. Services never import the ORM or hold sessions: repositories
arrive as instances bound to a unit of work by the composition root
(`runtime/`), and persistence goes through schema-accepting repository
methods.

Dependency rule: depends on collectors, agents, repositories, schemas,
logging, core. NEVER on models.
"""

from ai_oip.services.problem_discovery import ProblemDiscoveryService
from ai_oip.services.report import render_markdown_report

__all__ = ["ProblemDiscoveryService", "render_markdown_report"]

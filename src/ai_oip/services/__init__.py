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

from ai_oip.services.competition_research import CompetitionResearchService
from ai_oip.services.opportunity_scoring import (
    DEFAULT_WEIGHTS,
    OpportunityScoringService,
    weighted_total,
)
from ai_oip.services.problem_discovery import ProblemDiscoveryService
from ai_oip.services.product_recommendation import ProductRecommendationService
from ai_oip.services.report import (
    render_competition_report,
    render_markdown_report,
    render_opportunity_report,
    render_recommendation_report,
    render_workflow_report,
)
from ai_oip.services.workflow_discovery import WorkflowDiscoveryService

__all__ = [
    "DEFAULT_WEIGHTS",
    "CompetitionResearchService",
    "OpportunityScoringService",
    "ProblemDiscoveryService",
    "ProductRecommendationService",
    "WorkflowDiscoveryService",
    "render_competition_report",
    "render_markdown_report",
    "render_opportunity_report",
    "render_recommendation_report",
    "render_workflow_report",
    "weighted_total",
]

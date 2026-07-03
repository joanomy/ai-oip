"""Repositories: the ONLY layer allowed to query the database.

Wraps `models/` behind explicit methods (e.g., get_by_id, save). Services
and pipelines depend on repositories; agents never do.

`SQLAlchemyRepository` is the generic, reusable implementation every
concrete repository should use or subclass rather than reimplementing
CRUD against the database.

Dependency rule: depends on models, core.
"""

from ai_oip.repositories.base import BaseRepository
from ai_oip.repositories.competition_repository import CompetitionRepository
from ai_oip.repositories.opportunity_repository import OpportunityRepository
from ai_oip.repositories.problem_repository import ProblemRepository
from ai_oip.repositories.product_recommendation_repository import ProductRecommendationRepository
from ai_oip.repositories.sqlalchemy_repository import SQLAlchemyRepository
from ai_oip.repositories.workflow_repository import WorkflowRepository

__all__ = [
    "BaseRepository",
    "CompetitionRepository",
    "OpportunityRepository",
    "ProblemRepository",
    "ProductRecommendationRepository",
    "SQLAlchemyRepository",
    "WorkflowRepository",
]

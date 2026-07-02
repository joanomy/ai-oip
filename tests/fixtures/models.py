"""Test-only ORM model.

Exists solely to exercise `SQLAlchemyRepository` against a real
database engine in tests. This is not a business entity — no real
domain model should be added here or copied from here; it demonstrates
the *pattern* every real model + repository will follow once concrete
business models exist.
"""

from sqlalchemy.orm import Mapped, mapped_column

from ai_oip.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class DemoRecord(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Minimal model: one column, used only to prove the repository works."""

    __tablename__ = "demo_records"

    value: Mapped[str] = mapped_column(nullable=False)

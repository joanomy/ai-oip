"""Shared stage-composition frame (ADR-0014).

Every pipeline stage repeats the same lifecycle: resolve Settings /
engine / provider / prompt loader (production defaults unless a test
injects overrides), open one unit-of-work session, dispose the engine
afterwards only if this run created it. That frame lives here, once —
stage modules contribute only their agent, repositories, and service
wiring.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from ai_oip.config import Settings, get_settings
from ai_oip.models import create_engine_from_settings, create_session_factory, session_scope
from ai_oip.prompts import PromptLoader
from ai_oip.providers import LLMProvider, anthropic_provider_from_settings


@dataclass(frozen=True)
class StageContext:
    """Resolved dependencies plus the open unit-of-work session."""

    session: AsyncSession
    provider: LLMProvider
    prompt_loader: PromptLoader
    settings: Settings


@asynccontextmanager
async def stage_context(
    *,
    settings: Settings | None = None,
    engine: AsyncEngine | None = None,
    provider: LLMProvider | None = None,
    prompt_loader: PromptLoader | None = None,
) -> AsyncIterator[StageContext]:
    """Resolve stage dependencies and manage the unit-of-work lifecycle.

    None means "wire the production default from Settings" — the same
    override seams every stage has exposed since the walking skeleton.
    The engine is disposed on exit only when this context created it.
    """
    settings = settings if settings is not None else get_settings()
    owns_engine = engine is None
    engine = engine if engine is not None else create_engine_from_settings(settings)
    try:
        provider = provider if provider is not None else anthropic_provider_from_settings(settings)
        loader = prompt_loader if prompt_loader is not None else PromptLoader()
        session_factory = create_session_factory(engine)
        async with session_scope(session_factory) as session:
            yield StageContext(
                session=session,
                provider=provider,
                prompt_loader=loader,
                settings=settings,
            )
    finally:
        if owns_engine:
            await engine.dispose()

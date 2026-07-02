# Runtime image for AI-OIP. Built on uv's layered pattern: dependencies
# install from the lockfile in their own (highly cacheable) layer before
# the project source is copied.
#
# No application entrypoint exists yet — the walking-skeleton milestone
# adds the first one; until then the CMD is an import smoke check so the
# image is verifiable in CI.

FROM python:3.12-slim AS runtime

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1

# Dependency layer: lockfile only, no project source — rebuilt only
# when dependencies actually change.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Project layer. README.md is required: pyproject declares it as the
# package readme, so the hatchling build fails without it.
COPY README.md ./
COPY src ./src
COPY alembic.ini ./
COPY migrations ./migrations
RUN uv sync --frozen --no-dev

# Non-root runtime user.
RUN useradd --create-home appuser && chown -R appuser:appuser /app
USER appuser

CMD ["uv", "run", "--no-sync", "python", "-c", "import ai_oip; print(f'ai-oip {ai_oip.__version__} runtime image OK')"]

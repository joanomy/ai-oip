"""Unit tests for typed application settings (Milestone 2).

Covers: defaults, environment variable overrides, fail-fast validation
on bad input, the production+debug guard, and get_settings() caching
behavior.
"""

import pytest
from pydantic import ValidationError

from ai_iop.config import Environment, Settings, get_settings


def test_defaults_are_safe_for_local_development() -> None:
    settings = Settings(_env_file=None)

    assert settings.environment is Environment.DEVELOPMENT
    assert settings.debug is False
    assert settings.is_development is True
    assert settings.is_production is False


def test_environment_accepts_valid_values(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENVIRONMENT", "staging")

    settings = Settings(_env_file=None)

    assert settings.environment is Environment.STAGING


def test_invalid_environment_value_fails_fast(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENVIRONMENT", "not_a_real_environment")

    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_debug_true_in_production_is_rejected() -> None:
    with pytest.raises(ValidationError, match="debug must be False"):
        Settings(_env_file=None, environment=Environment.PRODUCTION, debug=True)


def test_debug_false_in_production_is_allowed() -> None:
    settings = Settings(_env_file=None, environment=Environment.PRODUCTION, debug=False)

    assert settings.is_production is True
    assert settings.debug is False


def test_get_settings_returns_cached_singleton() -> None:
    get_settings.cache_clear()

    first = get_settings()
    second = get_settings()

    assert first is second


def test_get_settings_cache_clear_allows_reload(monkeypatch: pytest.MonkeyPatch) -> None:
    get_settings.cache_clear()
    first = get_settings()

    monkeypatch.setenv("APP_NAME", "Reloaded-Name")
    get_settings.cache_clear()
    second = get_settings()

    assert first is not second
    assert second.app_name == "Reloaded-Name"

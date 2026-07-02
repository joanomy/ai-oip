"""Unit tests for structured logging (Milestone 3).

Uses structlog's own testing utilities (`capture_logs`) rather than
mocking, so these tests exercise the real configured pipeline —
level filtering, rendering, and structured field propagation.
"""

import structlog
import structlog.testing

from ai_oip.config import Environment, Settings
from ai_oip.logging import configure_logging, get_logger, is_configured, reset_logging


def test_configure_logging_sets_configured_flag() -> None:
    reset_logging()
    settings = Settings(_env_file=None)

    configure_logging(settings)

    assert is_configured() is True
    reset_logging()


def test_reset_logging_clears_configured_flag() -> None:
    configure_logging(Settings(_env_file=None))
    reset_logging()

    assert is_configured() is False


def test_log_events_carry_structured_fields_not_interpolated_strings() -> None:
    reset_logging()
    configure_logging(Settings(_env_file=None, log_level="INFO"))
    logger = get_logger("test.module")

    with structlog.testing.capture_logs() as captured:
        logger.info("agent_started", agent_name="summarizer", input_tokens=42)

    reset_logging()

    assert len(captured) == 1
    event = captured[0]
    assert event["event"] == "agent_started"
    assert event["agent_name"] == "summarizer"
    assert event["input_tokens"] == 42
    assert event["log_level"] == "info"


def test_log_level_filtering_drops_below_threshold_messages() -> None:
    reset_logging()
    configure_logging(Settings(_env_file=None, log_level="WARNING"))
    logger = get_logger("test.module")

    with structlog.testing.capture_logs() as captured:
        logger.info("this_should_be_dropped")
        logger.warning("this_should_appear")

    reset_logging()

    events = [entry["event"] for entry in captured]
    assert "this_should_be_dropped" not in events
    assert "this_should_appear" in events


def test_unknown_log_level_raises_at_configuration_time() -> None:
    import pytest

    reset_logging()
    settings = Settings(_env_file=None)
    # log_level is a plain str field, so an invalid value bypasses
    # pydantic validation and must be caught by configure_logging itself.
    object.__setattr__(settings, "log_level", "NOT_A_LEVEL")

    with pytest.raises(ValueError, match="Unknown log level"):
        configure_logging(settings)


def test_development_and_production_use_different_renderers() -> None:
    reset_logging()
    dev_settings = Settings(_env_file=None, environment=Environment.DEVELOPMENT)
    configure_logging(dev_settings)
    dev_processors = structlog.get_config()["processors"]
    reset_logging()

    prod_settings = Settings(_env_file=None, environment=Environment.PRODUCTION, debug=False)
    configure_logging(prod_settings)
    prod_processors = structlog.get_config()["processors"]
    reset_logging()

    assert type(dev_processors[-1]) is not type(prod_processors[-1])
    assert isinstance(prod_processors[-1], structlog.processors.JSONRenderer)

"""Config: typed application settings (Pydantic Settings).

Dependency rule: depends only on core. Nothing depends on config except
the application entrypoint and modules that need a specific setting
value passed to them explicitly (never by importing os.environ directly
— see settings.py for the enforcement mechanism).
"""

from ai_oip.config.settings import Environment, Settings, get_settings

__all__ = ["Environment", "Settings", "get_settings"]

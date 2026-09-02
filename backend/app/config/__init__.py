"""
RazorPulse Configuration Package.

Exports the application settings singleton.
"""

from app.config.settings import Settings, get_settings

__all__ = ["Settings", "get_settings"]

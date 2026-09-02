"""
Pytest configuration and shared fixtures.
"""

import os
import sys

import pytest

# Ensure the backend app is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(autouse=True)
def reset_settings_cache():
    """Clear the settings cache between tests to avoid stale config."""
    from app.config.settings import get_settings
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()

"""
Supabase client initialization.

Provides a singleton Supabase client for the backend.
Uses the SERVICE_ROLE key for server-side operations.

SECURITY:
  - The service role key is NEVER exposed to the frontend.
  - The service role key is NEVER logged.
"""

from typing import Optional

from supabase import Client, create_client

from app.config.settings import get_settings
from app.core.exceptions import ConfigurationError
from app.core.logging import get_logger

logger = get_logger("supabase_client")

_client: Optional[Client] = None


def get_supabase_client() -> Client:
    """
    Return the Supabase client singleton.

    Creates the client on first call. Uses the service role key
    for full database access (bypasses RLS).

    Raises:
        ConfigurationError: If Supabase credentials are not configured.
    """
    global _client

    if _client is not None:
        return _client

    settings = get_settings()

    if not settings.has_supabase_credentials():
        raise ConfigurationError(
            "Supabase credentials are not configured. "
            "Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in .env"
        )

    _client = create_client(
        supabase_url=settings.SUPABASE_URL,
        supabase_key=settings.SUPABASE_SERVICE_ROLE_KEY,
    )

    logger.info("Supabase client initialized")
    return _client


def reset_supabase_client() -> None:
    """Reset the client singleton (useful for testing)."""
    global _client
    _client = None

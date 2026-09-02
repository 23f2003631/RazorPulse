"""
Application configuration and settings.

Manages environment variables and application-wide configuration
using pydantic-settings for type-safe, validated configuration.

All secrets are loaded from environment variables or .env files.
Secrets are NEVER hard-coded or logged.
"""

from functools import lru_cache
from typing import Optional

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Determine backend directory and project root directory relative to this file
_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
_ROOT_DIR = _BACKEND_DIR.parent

# Env file precedence: root .env loaded first, then backend/.env overrides it
_ENV_FILES = [
    str(f) for f in [_ROOT_DIR / ".env", _BACKEND_DIR / ".env"] if f.exists()
] or [".env"]


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Variables are grouped by service. SECRET variables must never
    be exposed to the frontend or logged.
    """

    model_config = SettingsConfigDict(
        env_file=_ENV_FILES,
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # --- Application ---
    APP_NAME: str = "RazorPulse"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    ENVIRONMENT: str = Field(default="development", description="development | staging | production")

    # --- Razorpay (SECRET) ---
    # These are Razorpay Test Mode credentials.
    # RazorPulse does NOT execute payments or modify merchant state.
    RAZORPAY_KEY_ID: Optional[str] = Field(default=None, description="Razorpay Test Mode Key ID")
    RAZORPAY_KEY_SECRET: Optional[str] = Field(default=None, description="SECRET: Razorpay Test Mode Key Secret")
    RAZORPAY_WEBHOOK_SECRET: Optional[str] = Field(default=None, description="SECRET: Razorpay Webhook Secret")

    # --- Exa AI (SECRET) ---
    EXA_API_KEY: Optional[str] = Field(default=None, description="SECRET: Exa AI API Key")

    # --- Gemini (SECRET) ---
    GEMINI_API_KEY: Optional[str] = Field(default=None, description="SECRET: Google Gemini API Key")
    GEMINI_MODEL: str = Field(default="gemini-2.5-flash", description="Gemini model name for evidence verification")

    # --- Supabase ---
    SUPABASE_URL: Optional[str] = Field(default=None, description="Supabase project URL")
    SUPABASE_ANON_KEY: Optional[str] = Field(default=None, description="Supabase anonymous key (public, limited access)")
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = Field(
        default=None,
        description="SECRET: Supabase service role key. Server-side only. NEVER expose to frontend.",
    )

    # --- Database ---
    DATABASE_URL: Optional[str] = Field(default=None, description="Direct PostgreSQL connection URL")

    # --- Frontend ---
    NEXT_PUBLIC_API_URL: str = Field(default="http://localhost:8000", description="Public API URL for frontend")

    # --- API Configuration ---
    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="Allowed CORS origins",
    )

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    def has_exa_credentials(self) -> bool:
        """Check if Exa API key is configured (not just placeholder)."""
        return bool(self.EXA_API_KEY and not self.EXA_API_KEY.startswith("your_"))

    def has_gemini_credentials(self) -> bool:
        """Check if Gemini API key is configured (not just placeholder)."""
        return bool(self.GEMINI_API_KEY and not self.GEMINI_API_KEY.startswith("your_"))

    def has_supabase_credentials(self) -> bool:
        """Check if Supabase credentials are configured (not just placeholder)."""
        return bool(
            self.SUPABASE_URL
            and self.SUPABASE_SERVICE_ROLE_KEY
            and not self.SUPABASE_URL.startswith("https://your-")
            and not self.SUPABASE_SERVICE_ROLE_KEY.startswith("your_")
        )

    def has_razorpay_credentials(self) -> bool:
        """Check if Razorpay Test Mode credentials are configured."""
        return bool(
            self.RAZORPAY_KEY_ID
            and self.RAZORPAY_KEY_SECRET
            and not self.RAZORPAY_KEY_ID.startswith("rzp_test_placeholder")
            and not self.RAZORPAY_KEY_SECRET.startswith("your_")
        )


@lru_cache()
def get_settings() -> Settings:
    """
    Return a cached Settings instance.

    Uses lru_cache so environment variables are read only once.
    Call get_settings.cache_clear() if you need to reload.
    """
    return Settings()

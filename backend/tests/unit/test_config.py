"""
Unit tests for configuration loading.

Tests that the Settings class correctly loads and validates
environment variables.
"""

import os

import pytest

from app.config.settings import Settings


class TestSettings:
    """Test suite for application configuration."""

    def test_default_settings_load(self):
        """Settings should load with defaults when env vars are not set."""
        settings = Settings(
            _env_file=None,  # Don't load .env file
        )
        assert settings.APP_NAME == "RazorPulse"
        assert settings.APP_VERSION == "0.1.0"
        assert settings.ENVIRONMENT == "development"
        assert settings.DEBUG is False

    def test_app_name_default(self):
        """Default app name should be RazorPulse."""
        settings = Settings(_env_file=None)
        assert settings.APP_NAME == "RazorPulse"

    def test_is_development_default(self):
        """Default environment should be development."""
        settings = Settings(_env_file=None)
        assert settings.is_development is True
        assert settings.is_production is False

    def test_cors_origins_default(self):
        """Default CORS origins should include localhost."""
        settings = Settings(_env_file=None)
        assert "http://localhost:3000" in settings.CORS_ORIGINS
        assert "http://localhost:8000" in settings.CORS_ORIGINS

    def test_api_v1_prefix(self):
        """API v1 prefix should be /api/v1."""
        settings = Settings(_env_file=None)
        assert settings.API_V1_PREFIX == "/api/v1"

    def test_has_exa_credentials_placeholder(self):
        """Placeholder Exa key should report as not configured."""
        settings = Settings(
            _env_file=None,
            EXA_API_KEY="your_exa_api_key_here",
        )
        assert settings.has_exa_credentials() is False

    def test_has_exa_credentials_real(self):
        """A non-placeholder Exa key should report as configured."""
        settings = Settings(
            _env_file=None,
            EXA_API_KEY="real-key-abc123",
        )
        assert settings.has_exa_credentials() is True

    def test_has_gemini_credentials_placeholder(self):
        """Placeholder Gemini key should report as not configured."""
        settings = Settings(
            _env_file=None,
            GEMINI_API_KEY="your_gemini_api_key_here",
        )
        assert settings.has_gemini_credentials() is False

    def test_has_supabase_credentials_not_configured(self):
        """Missing Supabase credentials should report as not configured."""
        settings = Settings(_env_file=None)
        assert settings.has_supabase_credentials() is False

    def test_has_supabase_credentials_placeholder(self):
        """Placeholder Supabase credentials should report as not configured."""
        settings = Settings(
            _env_file=None,
            SUPABASE_URL="https://your-project.supabase.co",
            SUPABASE_SERVICE_ROLE_KEY="your_supabase_service_role_key_here",
        )
        assert settings.has_supabase_credentials() is False

    def test_has_razorpay_credentials_placeholder(self):
        """Placeholder Razorpay credentials should report as not configured."""
        settings = Settings(
            _env_file=None,
            RAZORPAY_KEY_ID="rzp_test_placeholder_key_id",
            RAZORPAY_KEY_SECRET="your_razorpay_key_secret_here",
        )
        assert settings.has_razorpay_credentials() is False

    def test_gemini_model_default(self):
        """Default Gemini model should be gemini-2.5-flash."""
        settings = Settings(_env_file=None)
        assert settings.GEMINI_MODEL == "gemini-2.5-flash"

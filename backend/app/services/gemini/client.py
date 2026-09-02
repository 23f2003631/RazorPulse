"""
Google Gemini client wrapper.

Gemini is used for EVIDENCE VERIFICATION AND INTERPRETATION —
assessing whether external evidence discovered by Exa credibly
explains an observed payment anomaly.

MODEL SELECTION:
  Using gemini-2.5-flash (as of September 2026).
  Rationale:
    - Cost-effective for prototype
    - Supports structured output via Pydantic schemas
    - Low latency
    - Sufficient reasoning capability for evidence assessment
  Can be upgraded to gemini-2.5-pro or gemini-3.x in future phases.

SDK:
  Using google-genai (unified SDK, replaces deprecated google-generativeai).

ARCHITECTURAL BOUNDARY:
  Gemini INTERPRETS evidence.
  It does NOT produce the final ECI score.
  It does NOT make financial decisions.
  The deterministic scoring engine uses Gemini's structured output
  as INPUT, not as the FINAL ANSWER.
"""

from typing import Optional

from pydantic import BaseModel, Field

from app.config.settings import get_settings
from app.core.exceptions import ConfigurationError, GeminiServiceError
from app.core.logging import get_logger

logger = get_logger("gemini_client")


class GeminiClient:
    """
    Wrapper around the Google Gen AI SDK for Gemini.

    Provides methods for evidence verification and interpretation.
    Day 1: Only connectivity verification. Full verification prompts
    will be implemented in a later phase.
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize the Gemini client.

        Args:
            api_key: Gemini API key. If not provided, reads from settings.
            model: Model name to use. If not provided, reads from settings.

        Raises:
            ConfigurationError: If no API key is available.
        """
        settings = get_settings()
        self._api_key = api_key or settings.GEMINI_API_KEY
        self._model_name = model or settings.GEMINI_MODEL

        if not self._api_key or self._api_key.startswith("your_"):
            raise ConfigurationError(
                "Gemini API key is not configured. Set GEMINI_API_KEY in .env"
            )

        try:
            from google import genai
            self._client = genai.Client(api_key=self._api_key)
        except ImportError:
            raise ConfigurationError("google-genai package is not installed")
        except Exception as e:
            raise GeminiServiceError(f"Failed to initialize Gemini client: {e}")

        logger.info("Gemini client initialized (model={})", self._model_name)

    def health_check(self) -> dict:
        """
        Verify Gemini API connectivity with a minimal test prompt.

        Uses a harmless prompt to confirm the API key works and the
        model responds correctly.

        Returns:
            Dict with connectivity status and model info.
        """
        try:
            response = self._client.models.generate_content(
                model=self._model_name,
                contents="Respond with exactly: RAZORPULSE_OK",
            )

            response_text = response.text.strip() if response.text else ""
            return {
                "status": "ok",
                "service": "gemini",
                "model": self._model_name,
                "response_preview": response_text[:50],
            }
        except Exception as e:
            logger.error("Gemini health check failed: {}", str(e))
            return {
                "status": "error",
                "service": "gemini",
                "model": self._model_name,
                "error": str(e),
            }

    def test_structured_output(self) -> dict:
        """
        Verify that Gemini supports structured output with Pydantic schemas.

        This confirms the capability we'll need for evidence verification
        in later phases.

        Returns:
            Dict with structured output test results.
        """

        class TestStructuredOutput(BaseModel):
            """Test schema for structured output verification."""
            message: str = Field(description="A test message")
            confidence: float = Field(description="A confidence score between 0 and 1")

        try:
            response = self._client.models.generate_content(
                model=self._model_name,
                contents="Return a test message with 'RazorPulse structured output works' and confidence 0.95",
                config={
                    "response_mime_type": "application/json",
                    "response_schema": TestStructuredOutput,
                },
            )

            import json
            parsed = json.loads(response.text)
            return {
                "status": "ok",
                "service": "gemini",
                "feature": "structured_output",
                "model": self._model_name,
                "parsed_response": parsed,
            }
        except Exception as e:
            logger.error("Gemini structured output test failed: {}", str(e))
            return {
                "status": "error",
                "service": "gemini",
                "feature": "structured_output",
                "model": self._model_name,
                "error": str(e),
            }

"""
Integration health check routes.

Provides endpoints to verify connectivity with external services
(Exa AI, Google Gemini). These are diagnostic endpoints for
development and testing — they do NOT expose API keys or secrets.
"""

from fastapi import APIRouter

from app.config.settings import get_settings
from app.core.logging import get_logger

logger = get_logger("integrations_route")

router = APIRouter(prefix="/api/v1/integrations", tags=["integrations"])


@router.get("/exa/health")
async def exa_health_check():
    """
    Verify Exa AI API connectivity.

    Attempts to initialize the Exa client and perform a minimal
    test query. Returns status without exposing the API key.
    """
    settings = get_settings()

    if not settings.has_exa_credentials():
        return {
            "status": "not_configured",
            "service": "exa",
            "message": "EXA_API_KEY is not set or is a placeholder",
        }

    try:
        from app.services.exa.client import ExaClient
        client = ExaClient()
        return client.health_check()
    except Exception as e:
        logger.error("Exa health check failed: {}", str(e))
        return {
            "status": "error",
            "service": "exa",
            "error": str(e),
        }


@router.get("/gemini/health")
async def gemini_health_check():
    """
    Verify Google Gemini API connectivity.

    Attempts to initialize the Gemini client and send a minimal
    test prompt. Returns status without exposing the API key.
    """
    settings = get_settings()

    if not settings.has_gemini_credentials():
        return {
            "status": "not_configured",
            "service": "gemini",
            "message": "GEMINI_API_KEY is not set or is a placeholder",
        }

    try:
        from app.services.gemini.client import GeminiClient
        client = GeminiClient()
        return client.health_check()
    except Exception as e:
        logger.error("Gemini health check failed: {}", str(e))
        return {
            "status": "error",
            "service": "gemini",
            "error": str(e),
        }


@router.get("/status")
async def integration_status():
    """
    Return the configuration status of all external integrations.

    Does NOT test connectivity — only checks if credentials are configured.
    """
    settings = get_settings()

    return {
        "supabase": {
            "configured": settings.has_supabase_credentials(),
        },
        "exa": {
            "configured": settings.has_exa_credentials(),
        },
        "gemini": {
            "configured": settings.has_gemini_credentials(),
            "model": settings.GEMINI_MODEL,
        },
        "razorpay": {
            "configured": settings.has_razorpay_credentials(),
            "note": "Test Mode only. No public risk webhook confirmed.",
        },
    }

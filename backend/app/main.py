"""
RazorPulse Backend Application Entry Point.

Initializes the FastAPI application, configures middleware,
and registers API routers.

RazorPulse is a READ-ONLY decision-support system.
It does NOT execute payments, modify merchant state, or make
autonomous financial decisions.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config.settings import get_settings
from app.core.exceptions import (
    RazorPulseError,
    ResourceNotFoundError,
    RiskEventValidationError,
)
from app.core.logging import get_logger, setup_logging

logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle."""
    settings = get_settings()
    setup_logging(debug=settings.DEBUG)

    logger.info("Starting RazorPulse v{}", settings.APP_VERSION)
    logger.info("Environment: {}", settings.ENVIRONMENT)

    # Log integration availability (never log actual keys)
    logger.info("Supabase configured: {}", settings.has_supabase_credentials())
    logger.info("Exa configured: {}", settings.has_exa_credentials())
    logger.info("Gemini configured: {}", settings.has_gemini_credentials())
    logger.info("Razorpay configured: {}", settings.has_razorpay_credentials())

    yield

    logger.info("RazorPulse shutting down")


def create_app() -> FastAPI:
    """
    Application factory.

    Creates and configures the FastAPI application instance.
    """
    settings = get_settings()

    app = FastAPI(
        title="RazorPulse",
        description=(
            "AI-powered external-context verification for anomalous "
            "payment-risk events. Decision-support only — no autonomous "
            "financial actions."
        ),
        version=settings.APP_VERSION,
        lifespan=lifespan,
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
    )

    # --- CORS ---
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    # --- Exception Handlers ---
    @app.exception_handler(RiskEventValidationError)
    async def validation_error_handler(request: Request, exc: RiskEventValidationError):
        return JSONResponse(
            status_code=422,
            content={"error": "validation_error", "message": exc.message},
        )

    @app.exception_handler(ResourceNotFoundError)
    async def not_found_handler(request: Request, exc: ResourceNotFoundError):
        return JSONResponse(
            status_code=404,
            content={
                "error": "not_found",
                "message": exc.message,
                "resource_type": exc.resource_type,
                "resource_id": exc.resource_id,
            },
        )

    @app.exception_handler(RazorPulseError)
    async def razorpulse_error_handler(request: Request, exc: RazorPulseError):
        logger.error("Application error: {}", exc.message)
        return JSONResponse(
            status_code=500,
            content={"error": "internal_error", "message": "An internal error occurred"},
        )

    # --- Routes ---
    # Import here to avoid circular imports
    from app.api.routes.health import router as health_router
    from app.api.routes.risk_events import router as risk_events_router
    from app.api.routes.integrations import router as integrations_router

    app.include_router(health_router)
    app.include_router(risk_events_router)
    app.include_router(integrations_router)

    return app


# Create the application instance
app = create_app()

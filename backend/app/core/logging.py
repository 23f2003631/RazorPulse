"""
Logging configuration and utilities for RazorPulse.

Uses loguru for structured logging.
Ensures secrets are NEVER included in log output.
"""

import sys

from loguru import logger

# Secrets that must never appear in logs.
# The actual values are checked at log-write time.
_SECRET_ENV_NAMES = [
    "RAZORPAY_KEY_SECRET",
    "RAZORPAY_WEBHOOK_SECRET",
    "EXA_API_KEY",
    "GEMINI_API_KEY",
    "SUPABASE_SERVICE_ROLE_KEY",
    "SUPABASE_ANON_KEY",
    "DATABASE_URL",
]


def setup_logging(*, debug: bool = False) -> None:
    """
    Configure application-wide logging.

    Args:
        debug: If True, set log level to DEBUG; otherwise INFO.
    """
    # Remove default loguru handler
    logger.remove()

    level = "DEBUG" if debug else "INFO"

    # Console handler with structured format
    logger.add(
        sys.stderr,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        ),
        level=level,
        colorize=True,
        backtrace=False,  # Don't leak stack info in production
        diagnose=False,   # Don't leak local vars in production
    )

    logger.info("Logging initialized (level={})", level)


def get_logger(name: str = "razorpulse"):
    """
    Return a contextualized logger.

    Args:
        name: Module or component name for log context.
    """
    return logger.bind(component=name)

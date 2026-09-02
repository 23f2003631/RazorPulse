"""
Gemini Transient Error Retry Utility.

Provides bounded exponential backoff retry for transient Google Gemini API failures
(e.g., HTTP 503 UNAVAILABLE, HTTP 429 RESOURCE_EXHAUSTED).

Does NOT retry permanent client errors (400, 401, 403, 404, validation errors).
"""

import re
import time
from typing import Callable, TypeVar

from google.genai.errors import APIError, ClientError, ServerError

from app.core.logging import get_logger

logger = get_logger("gemini_retry")

T = TypeVar("T")

# Transient status codes eligible for retry
RETRYABLE_STATUS_CODES = {429, 503, 504}

# Keywords indicating transient provider capacity/load issues
RETRYABLE_KEYWORDS = [
    "503",
    "429",
    "504",
    "unavailable",
    "resource_exhausted",
    "high demand",
    "experiencing high demand",
    "temporarily unavailable",
    "deadline expired",
    "rate limit",
    "quota exceeded",
    "spikes in demand",
]


def is_retryable_gemini_error(exc: Exception) -> bool:
    """
    Determine if an exception from Gemini API is a transient, retryable error.

    Retryable:
    - ServerError (503 UNAVAILABLE, 504 DEADLINE_EXCEEDED, 5xx)
    - APIError with code 429 (RESOURCE_EXHAUSTED) or 503/504
    - String matches for transient rate limits and capacity spikes

    Non-retryable:
    - ClientError (400 Bad Request, 401 Unauthorized, 403 Forbidden, 404 Not Found)
    - Validation errors, ValueError, TypeError, KeyError
    """
    # Explicit non-retryable client errors (except 429 which might be classified as ClientError or APIError)
    if isinstance(exc, ClientError):
        code = getattr(exc, "code", None)
        if code != 429:
            return False

    # Server errors (5xx) are retryable
    if isinstance(exc, ServerError):
        return True

    # Check APIError status codes
    if isinstance(exc, APIError):
        code = getattr(exc, "code", None)
        if code in RETRYABLE_STATUS_CODES:
            return True

    # Fallback to string inspection on error message for known transient signals
    err_msg = str(exc).lower()
    for kw in RETRYABLE_KEYWORDS:
        if kw in err_msg:
            return True

    return False


def _sanitize_error_message(exc: Exception) -> str:
    """Strip any potential API keys or credentials from error message string."""
    msg = str(exc)
    msg = re.sub(r"key=[A-Za-z0-9_\-]+", "key=[REDACTED]", msg)
    msg = re.sub(r"AIza[0-9A-Za-z-_]{35}", "[REDACTED_API_KEY]", msg)
    return msg


def with_gemini_retry(
    func: Callable[[], T],
    max_attempts: int = 3,
    initial_delay_seconds: float = 2.0,
    backoff_multiplier: float = 2.0,
    operation_name: str = "gemini_request",
) -> T:
    """
    Execute a Gemini operation with bounded exponential backoff on transient errors.

    Args:
        func: Zero-argument callable executing the Gemini API request
        max_attempts: Maximum number of attempts (default: 3)
        initial_delay_seconds: Delay before first retry in seconds (default: 2.0s)
        backoff_multiplier: Exponential multiplier per retry (default: 2.0)
        operation_name: Human-readable name for logging context

    Returns:
        Result of successful func() invocation

    Raises:
        Exception: The last caught exception if all retry attempts fail,
                   or immediately if the error is non-retryable.
    """
    attempt = 1
    current_delay = initial_delay_seconds

    while True:
        try:
            return func()
        except Exception as exc:
            if is_retryable_gemini_error(exc) and attempt < max_attempts:
                logger.warning(
                    "Transient Gemini failure during {} (attempt {}/{}): {}. Retrying in {:.1f}s...",
                    operation_name,
                    attempt,
                    max_attempts,
                    _sanitize_error_message(exc),
                    current_delay,
                )
                time.sleep(current_delay)
                attempt += 1
                current_delay *= backoff_multiplier
            else:
                if attempt >= max_attempts and is_retryable_gemini_error(exc):
                    logger.error(
                        "Gemini {} exhausted all {} attempts. Last error: {}",
                        operation_name,
                        max_attempts,
                        _sanitize_error_message(exc),
                    )
                raise exc

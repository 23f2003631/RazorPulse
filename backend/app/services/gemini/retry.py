"""
Gemini Transient Error Retry Utility.

Provides bounded exponential backoff and server-specified retryDelay handling
for transient Google Gemini API failures (e.g., HTTP 503 UNAVAILABLE, transient 429 RESOURCE_EXHAUSTED).

Does NOT retry permanent client errors (400, 401, 403, 404, validation errors)
or non-transient daily quota exhaustion (e.g. GenerateRequestsPerDay limit reached).
"""

import re
import time
from typing import Callable, Optional, TypeVar

from google.genai.errors import APIError, ClientError, ServerError

from app.core.logging import get_logger

logger = get_logger("gemini_retry")

T = TypeVar("T")

# Maximum duration (seconds) we are willing to wait for a server-provided retryDelay
MAX_RETRY_DELAY_SECONDS = 60.0

# Transient status codes eligible for retry
RETRYABLE_STATUS_CODES = {429, 503, 504}

# Signals indicating daily or total account quota exhaustion (DO NOT RETRY)
DAILY_QUOTA_KEYWORDS = [
    "generaterequestsperday",
    "generate_content_free_tier_requests",
    "exceeded your current quota",
    "quota exceeded for metric",
    "free tier requests per day",
    "daily quota exceeded",
    "billing not enabled",
]

# Signals indicating transient provider capacity/load issues
TRANSIENT_KEYWORDS = [
    "503",
    "504",
    "unavailable",
    "resource_exhausted",
    "high demand",
    "experiencing high demand",
    "temporarily unavailable",
    "deadline expired",
    "rate limit",
    "spikes in demand",
]


def is_daily_quota_exhaustion_error(exc: Exception) -> bool:
    """
    Determine if an error represents a daily/account quota exhaustion.
    These are permanent for the current day and must NOT be retried.
    """
    err_msg = str(exc).lower()
    for kw in DAILY_QUOTA_KEYWORDS:
        if kw in err_msg:
            return True
    return False


def extract_retry_delay(exc: Exception) -> Optional[float]:
    """
    Extract server-provided retryDelay if present in error message or payload.
    Example formats:
    - retryDelay: '55s'
    - "retryDelay": "55.2s"
    - "retry in 55 seconds"
    """
    err_msg = str(exc)
    # Match retryDelay: '55s' or "retryDelay": "55s" or retryDelay: 55
    match = re.search(r"retryDelay['\":\s]+(\d+(?:\.\d+)?)\s*s?", err_msg, re.IGNORECASE)
    if match:
        try:
            return float(match.group(1))
        except (ValueError, IndexError):
            pass

    # Match "retry after 55s" or "retry in 55 seconds"
    match2 = re.search(r"retry\s+(?:after|in)\s+(\d+(?:\.\d+)?)\s*(?:s|sec|seconds)?", err_msg, re.IGNORECASE)
    if match2:
        try:
            return float(match2.group(1))
        except (ValueError, IndexError):
            pass

    return None


def is_retryable_gemini_error(exc: Exception) -> bool:
    """
    Determine if an exception from Gemini API is a transient, retryable error.

    Retryable:
    - ServerError (503 UNAVAILABLE, 504 DEADLINE_EXCEEDED, 5xx)
    - APIError with code 429 (RESOURCE_EXHAUSTED) or 503/504 (unless daily quota is exhausted)
    - String matches for transient rate limits and capacity spikes

    Non-retryable:
    - Daily/hard quota exhaustion (GenerateRequestsPerDay)
    - ClientError (400 Bad Request, 401 Unauthorized, 403 Forbidden, 404 Not Found)
    - Validation errors, ValueError, TypeError, KeyError
    """
    # 1. Daily quota exhaustion is never retryable
    if is_daily_quota_exhaustion_error(exc):
        return False

    # 2. Explicit non-retryable client errors (except 429 which might be in ClientError or APIError)
    if isinstance(exc, ClientError):
        code = getattr(exc, "code", None)
        if code != 429:
            return False

    # 3. Server errors (5xx) are retryable
    if isinstance(exc, ServerError):
        return True

    # 4. Check APIError status codes
    if isinstance(exc, APIError):
        code = getattr(exc, "code", None)
        if code in RETRYABLE_STATUS_CODES:
            return True

    # 5. Fallback to string inspection on error message for known transient signals
    err_msg = str(exc).lower()
    for kw in TRANSIENT_KEYWORDS:
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
    max_retry_delay_seconds: float = MAX_RETRY_DELAY_SECONDS,
    operation_name: str = "gemini_request",
) -> T:
    """
    Execute a Gemini operation with bounded retry and server-specified delay handling.

    Args:
        func: Zero-argument callable executing the Gemini API request
        max_attempts: Maximum number of attempts (default: 3)
        initial_delay_seconds: Delay before first retry in seconds (default: 2.0s)
        backoff_multiplier: Exponential multiplier per retry (default: 2.0)
        max_retry_delay_seconds: Maximum tolerable server delay (default: 60.0s)
        operation_name: Human-readable name for logging context

    Returns:
        Result of successful func() invocation

    Raises:
        Exception: The last caught exception if all retry attempts fail,
                   or immediately if the error is non-retryable or quota exhausted.
    """
    attempt = 1
    current_delay = initial_delay_seconds

    while True:
        try:
            return func()
        except Exception as exc:
            # Check 1: Daily quota exhaustion -> fail immediately without retry loop
            if is_daily_quota_exhaustion_error(exc):
                logger.error(
                    "Gemini daily quota exhausted during {}: {}. Non-retryable provider limit.",
                    operation_name,
                    _sanitize_error_message(exc),
                )
                raise exc

            # Check 2: Transient retryable failure
            if is_retryable_gemini_error(exc) and attempt < max_attempts:
                # Check for server-provided retry delay
                server_delay = extract_retry_delay(exc)
                if server_delay is not None:
                    if server_delay > max_retry_delay_seconds:
                        logger.error(
                            "Gemini server requested retry delay of {:.1f}s exceeding max limit ({:.1f}s) for {}. Failing immediately.",
                            server_delay,
                            max_retry_delay_seconds,
                            operation_name,
                        )
                        raise exc
                    sleep_duration = server_delay
                    logger.warning(
                        "Gemini rate limit with server retry delay ({:.1f}s) during {} (attempt {}/{}). Waiting...",
                        sleep_duration,
                        operation_name,
                        attempt,
                        max_attempts,
                    )
                else:
                    sleep_duration = current_delay
                    logger.warning(
                        "Transient Gemini failure during {} (attempt {}/{}): {}. Retrying in {:.1f}s...",
                        operation_name,
                        attempt,
                        max_attempts,
                        _sanitize_error_message(exc),
                        sleep_duration,
                    )

                time.sleep(sleep_duration)
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

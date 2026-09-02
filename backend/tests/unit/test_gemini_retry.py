"""
Unit tests for Gemini transient retry mechanism and quota handling.

Verifies bounded exponential backoff on 503/429 errors, immediate failure
on non-retryable errors and daily quota exhaustion, server retryDelay respect,
and proper attempt bounding without consuming API credits.
"""

from unittest.mock import MagicMock, call, patch
import pytest
from google.genai.errors import APIError, ClientError, ServerError
from pydantic import BaseModel, Field

from app.services.gemini.retry import (
    extract_retry_delay,
    is_daily_quota_exhaustion_error,
    is_retryable_gemini_error,
    with_gemini_retry,
)


class TestGeminiRetryClassification:
    """Test classification of retryable vs non-retryable errors."""

    def test_503_server_error_is_retryable(self):
        err = ServerError(503, "This model is currently experiencing high demand.")
        assert is_retryable_gemini_error(err) is True

    def test_504_deadline_exceeded_is_retryable(self):
        err = ServerError(504, "Deadline expired before operation could complete.")
        assert is_retryable_gemini_error(err) is True

    def test_429_resource_exhausted_is_retryable(self):
        err = APIError(429, "Quota exceeded or rate limit reached.")
        assert is_retryable_gemini_error(err) is True

    def test_string_matching_transient_keywords_is_retryable(self):
        err = Exception("503 UNAVAILABLE: Spikes in demand are usually temporary.")
        assert is_retryable_gemini_error(err) is True

    def test_daily_quota_exhaustion_is_not_retryable(self):
        err1 = APIError(429, "ResourceExhausted: GenerateRequestsPerDay quota exceeded")
        err2 = APIError(429, "Quota exceeded for quota metric 'generate_content_free_tier_requests'")
        err3 = Exception("You exceeded your current quota, please check your plan and billing details.")

        assert is_daily_quota_exhaustion_error(err1) is True
        assert is_daily_quota_exhaustion_error(err2) is True
        assert is_daily_quota_exhaustion_error(err3) is True

        assert is_retryable_gemini_error(err1) is False
        assert is_retryable_gemini_error(err2) is False
        assert is_retryable_gemini_error(err3) is False

    def test_extract_retry_delay_formats(self):
        err1 = Exception("ResourceExhausted: Please retry in 55 seconds (retryDelay: '55s')")
        err2 = Exception('{"error": {"code": 429, "message": "rate limit", "details": [{"retryDelay": "42.5s"}]}}')
        err3 = Exception("Please retry after 30s")
        err4 = Exception("Plain 503 error without delay info")

        assert extract_retry_delay(err1) == 55.0
        assert extract_retry_delay(err2) == 42.5
        assert extract_retry_delay(err3) == 30.0
        assert extract_retry_delay(err4) is None

    def test_400_client_error_is_not_retryable(self):
        err = ClientError(400, "Invalid argument: contents is required.")
        assert is_retryable_gemini_error(err) is False

    def test_401_unauthorized_is_not_retryable(self):
        err = ClientError(401, "API key not valid.")
        assert is_retryable_gemini_error(err) is False

    def test_403_forbidden_is_not_retryable(self):
        err = ClientError(403, "Permission denied.")
        assert is_retryable_gemini_error(err) is False

    def test_404_not_found_is_not_retryable(self):
        err = ClientError(404, "Model not found.")
        assert is_retryable_gemini_error(err) is False

    def test_validation_error_is_not_retryable(self):
        err = ValueError("Invalid response JSON structure")
        assert is_retryable_gemini_error(err) is False


class TestWithGeminiRetryExecution:
    """Test retry execution, backoff timing, and attempt bounding."""

    @patch("time.sleep", return_value=None)
    def test_successful_request_first_attempt(self, mock_sleep):
        """A successful call on attempt 1 returns immediately without sleep."""
        mock_func = MagicMock(return_value="success_result")
        result = with_gemini_retry(
            mock_func,
            max_attempts=3,
            initial_delay_seconds=0.1,
        )
        assert result == "success_result"
        assert mock_func.call_count == 1
        mock_sleep.assert_not_called()

    @patch("time.sleep", return_value=None)
    def test_503_followed_by_successful_retry(self, mock_sleep):
        """A 503 error on attempt 1 retries and succeeds on attempt 2."""
        mock_func = MagicMock(
            side_effect=[
                ServerError(503, "This model is currently experiencing high demand."),
                "success_after_503",
            ]
        )
        result = with_gemini_retry(
            mock_func,
            max_attempts=3,
            initial_delay_seconds=1.0,
            backoff_multiplier=2.0,
        )
        assert result == "success_after_503"
        assert mock_func.call_count == 2
        mock_sleep.assert_called_once_with(1.0)

    @patch("time.sleep", return_value=None)
    def test_429_with_server_retry_delay_respected(self, mock_sleep):
        """A 429 error containing retryDelay: '45s' sleeps for 45s and retries."""
        mock_func = MagicMock(
            side_effect=[
                APIError(429, "ResourceExhausted: rate limit reached (retryDelay: '45s')"),
                "success_after_server_delay",
            ]
        )
        result = with_gemini_retry(
            mock_func,
            max_attempts=3,
            initial_delay_seconds=1.0,
            max_retry_delay_seconds=60.0,
        )
        assert result == "success_after_server_delay"
        assert mock_func.call_count == 2
        mock_sleep.assert_called_once_with(45.0)

    @patch("time.sleep", return_value=None)
    def test_daily_quota_exhaustion_fails_immediately_without_retry(self, mock_sleep):
        """Daily quota error fails immediately on attempt 1 with zero retries."""
        mock_func = MagicMock(
            side_effect=APIError(429, "ResourceExhausted: GenerateRequestsPerDay quota exceeded")
        )
        with pytest.raises(APIError) as exc_info:
            with_gemini_retry(
                mock_func,
                max_attempts=3,
                initial_delay_seconds=1.0,
            )
        assert "GenerateRequestsPerDay" in str(exc_info.value)
        assert mock_func.call_count == 1
        mock_sleep.assert_not_called()

    @patch("time.sleep", return_value=None)
    def test_429_followed_by_successful_retry(self, mock_sleep):
        """A 429 error on attempts 1 and 2 without explicit server delay retries with exponential backoff."""
        mock_func = MagicMock(
            side_effect=[
                APIError(429, "Rate limit exceeded"),
                APIError(429, "Rate limit exceeded"),
                "success_after_429",
            ]
        )
        result = with_gemini_retry(
            mock_func,
            max_attempts=3,
            initial_delay_seconds=1.0,
            backoff_multiplier=2.0,
        )
        assert result == "success_after_429"
        assert mock_func.call_count == 3
        assert mock_sleep.call_count == 2
        mock_sleep.assert_has_calls([call(1.0), call(2.0)])

    @patch("time.sleep", return_value=None)
    def test_all_retry_attempts_exhausted(self, mock_sleep):
        """When all attempts fail with 503, the original error is raised."""
        mock_func = MagicMock(
            side_effect=ServerError(503, "Unavailable")
        )
        with pytest.raises(ServerError) as exc_info:
            with_gemini_retry(
                mock_func,
                max_attempts=3,
                initial_delay_seconds=0.5,
                backoff_multiplier=2.0,
            )
        assert "Unavailable" in str(exc_info.value)
        assert mock_func.call_count == 3
        assert mock_sleep.call_count == 2

    @patch("time.sleep", return_value=None)
    def test_non_retryable_error_not_retried(self, mock_sleep):
        """A 400 ClientError fails immediately on attempt 1 with zero retries."""
        mock_func = MagicMock(
            side_effect=ClientError(400, "Bad Request: invalid schema")
        )
        with pytest.raises(ClientError) as exc_info:
            with_gemini_retry(
                mock_func,
                max_attempts=3,
                initial_delay_seconds=1.0,
            )
        assert "Bad Request" in str(exc_info.value)
        assert mock_func.call_count == 1
        mock_sleep.assert_not_called()

# Gemini — Evidence verification and interpretation service
from app.services.gemini.client import GeminiClient
from app.services.gemini.prompts import (
    VERIFICATION_SYSTEM_INSTRUCTION,
    build_batch_evidence_verification_prompt,
    build_evidence_verification_prompt,
)
from app.services.gemini.retry import (
    extract_retry_delay,
    is_daily_quota_exhaustion_error,
    is_retryable_gemini_error,
    with_gemini_retry,
)
from app.services.gemini.schemas import EvidenceRelevanceAssessment
from app.services.gemini.verifier import (
    GeminiVerifier,
    rank_evidence_item,
    select_top_evidence,
)

__all__ = [
    "GeminiClient",
    "GeminiVerifier",
    "rank_evidence_item",
    "select_top_evidence",
    "EvidenceRelevanceAssessment",
    "VERIFICATION_SYSTEM_INSTRUCTION",
    "build_evidence_verification_prompt",
    "build_batch_evidence_verification_prompt",
    "with_gemini_retry",
    "is_retryable_gemini_error",
    "is_daily_quota_exhaustion_error",
    "extract_retry_delay",
]

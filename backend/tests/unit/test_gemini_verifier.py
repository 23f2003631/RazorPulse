"""
Unit tests for Gemini Evidence Verifier schemas and prompts.
"""

from uuid import uuid4
import pytest

from app.schemas.verification import (
    EvidenceStrength,
    EvidenceVerificationItem,
    ExplanationSupportLevel,
    MerchantMatchLevel,
    SourceCredibilityLevel,
    TemporalMatchLevel,
    VerificationResult,
)
from app.services.gemini.prompts import build_evidence_verification_prompt


class TestGeminiVerification:
    """Test suite for Gemini verification schemas and prompt construction."""

    def test_build_verification_prompt_formatting(self):
        """Prompt builder should inject all context and constraints cleanly."""
        prompt = build_evidence_verification_prompt(
            merchant_name="UrbanCraft India",
            merchant_domain="urbancraft.in",
            anomaly_type="transaction_velocity_spike",
            occurred_at_str="2026-08-28T14:30:00+05:30",
            risk_reason="17x velocity spike",
            evidence_id="12345678-1234-5678-1234-567812345678",
            evidence_url="https://yourstory.com/article",
            evidence_title="Viral Sale Event",
            source_domain="yourstory.com",
            source_type="news_media",
            published_at="2026-08-28T10:00:00Z",
            content_snippet="UrbanCraft India held a nationwide artisan festive launch.",
            highlights=["artisan festive launch", "huge spike"],
        )

        assert "UrbanCraft India" in prompt
        assert "urbancraft.in" in prompt
        assert "transaction_velocity_spike" in prompt
        assert "2026-08-28" in prompt
        assert "12345678-1234-5678-1234-567812345678" in prompt
        assert "artisan festive launch" in prompt
        assert "STRICT EVIDENCE GROUNDING" in prompt or "INSTRUCTIONS" in prompt

    def test_evidence_verification_item_validation(self):
        """Should successfully parse and validate a structured verification assessment."""
        ev_id = uuid4()
        item = EvidenceVerificationItem(
            evidence_id=ev_id,
            merchant_match=MerchantMatchLevel.DIRECT_MATCH,
            temporal_match=TemporalMatchLevel.EXACT_MATCH,
            explanation_support=ExplanationSupportLevel.STRONG_EXPLANATION,
            evidence_strength=EvidenceStrength.STRONG_DIRECT,
            source_credibility=SourceCredibilityLevel.HIGH,
            event_category="flash_sale",
            key_facts=["Sale launched Aug 28", "10x order volume recorded"],
            contradictions_identified=[],
            uncertainties_noted=[],
            reasoning_summary="Article directly verifies flash sale on anomaly date.",
        )

        assert item.evidence_id == ev_id
        assert item.merchant_match == MerchantMatchLevel.DIRECT_MATCH
        assert item.temporal_match == TemporalMatchLevel.EXACT_MATCH
        assert item.explanation_support == ExplanationSupportLevel.STRONG_EXPLANATION
        assert len(item.key_facts) == 2

    def test_verification_result_aggregation(self):
        """VerificationResult should store consolidated contradictions and item lists."""
        inv_id = uuid4()
        item1 = EvidenceVerificationItem(
            evidence_id=uuid4(),
            merchant_match=MerchantMatchLevel.DIRECT_MATCH,
            temporal_match=TemporalMatchLevel.EXACT_MATCH,
            explanation_support=ExplanationSupportLevel.STRONG_EXPLANATION,
            evidence_strength=EvidenceStrength.STRONG_DIRECT,
            source_credibility=SourceCredibilityLevel.HIGH,
            event_category="press_news",
            key_facts=["Confirmed launch"],
            contradictions_identified=["Minor typo in pricing"],
            uncertainties_noted=["Exact revenue not disclosed"],
            reasoning_summary="Verified.",
        )

        result = VerificationResult(
            investigation_id=inv_id,
            items=[item1],
            overall_contradictions=["Minor typo in pricing"],
            overall_uncertainties=["Exact revenue not disclosed"],
            verified_at_timestamp="2026-08-28T15:00:00Z",
        )

        assert result.investigation_id == inv_id
        assert len(result.items) == 1
        assert len(result.overall_contradictions) == 1
        assert len(result.overall_uncertainties) == 1

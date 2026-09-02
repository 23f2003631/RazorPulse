"""
Unit tests for Gemini Evidence Verifier schemas, prompts, deterministic selection, and batch verification.
"""

from unittest.mock import MagicMock, patch
from uuid import uuid4
import json
import pytest

from app.schemas.evidence import NormalizedEvidence, SourceType
from app.schemas.verification import (
    BatchEvidenceVerificationResponse,
    EvidenceStrength,
    EvidenceVerificationItem,
    ExplanationSupportLevel,
    MerchantMatchLevel,
    SourceCredibilityLevel,
    TemporalMatchLevel,
    VerificationResult,
    VerificationStatus,
)
from app.services.gemini.prompts import (
    build_batch_evidence_verification_prompt,
    build_evidence_verification_prompt,
)
from app.services.gemini.verifier import (
    GeminiVerifier,
    rank_evidence_item,
    select_top_evidence,
)


class TestGeminiVerification:
    """Test suite for Gemini verification schemas, selection, and batch execution."""

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

    def test_build_batch_evidence_verification_prompt(self):
        """Batch prompt builder should include all evidence items in one structured prompt."""
        ev1 = NormalizedEvidence(
            evidence_id=uuid4(),
            url="https://domain1.com/sale",
            title="Sale 1",
            source_domain="domain1.com",
            source_type=SourceType.MERCHANT_OFFICIAL,
            published_at="2026-08-28T10:00:00Z",
            content_snippet="Launch announcement.",
            highlights=["launch"],
            discovery_query="domain1 sale",
            discovery_query_intent="commercial_campaign",
        )
        ev2 = NormalizedEvidence(
            evidence_id=uuid4(),
            url="https://domain2.com/news",
            title="News 2",
            source_domain="domain2.com",
            source_type=SourceType.NEWS_MEDIA,
            published_at="2026-08-28T11:00:00Z",
            content_snippet="Viral reporting.",
            highlights=["viral reporting"],
            discovery_query="domain2 news",
            discovery_query_intent="news_coverage",
        )

        prompt = build_batch_evidence_verification_prompt(
            merchant_name="UrbanCraft India",
            merchant_domain="urbancraft.in",
            anomaly_type="transaction_velocity_spike",
            occurred_at_str="2026-08-28T14:30:00+05:30",
            risk_reason="17x velocity spike",
            evidence_items=[ev1, ev2],
        )

        assert "DISCOVERED EVIDENCE ITEMS (2 total to evaluate)" in prompt
        assert str(ev1.evidence_id) in prompt
        assert str(ev2.evidence_id) in prompt
        assert "BatchEvidenceVerificationResponse" in prompt

    def test_select_top_evidence_ranks_and_limits_correctly(self):
        """9 evidence items must partition into top 4 selected and 5 skipped."""
        items = []
        for i in range(9):
            source_type = SourceType.MERCHANT_OFFICIAL if i < 2 else (SourceType.NEWS_MEDIA if i < 5 else SourceType.GENERAL_WEB)
            items.append(
                NormalizedEvidence(
                    evidence_id=uuid4(),
                    url=f"https://source{i}.com/page",
                    title=f"Title {i}",
                    source_domain=f"source{i}.com",
                    source_type=source_type,
                    published_at=f"2026-08-{20+i}T00:00:00Z",
                    content_snippet=f"Snippet content for item {i} with some length",
                    highlights=[f"highlight {i}"] if i % 2 == 0 else [],
                    external_score=0.9 - (i * 0.05),
                    discovery_query=f"query {i}",
                    discovery_query_intent="test_intent",
                )
            )

        selected, skipped = select_top_evidence(items, max_items=4)

        assert len(selected) == 4
        assert len(skipped) == 5
        # The top 2 official merchant sources should be selected
        assert selected[0].source_type == SourceType.MERCHANT_OFFICIAL
        assert selected[1].source_type == SourceType.MERCHANT_OFFICIAL

    def test_verify_all_evidence_performs_single_batch_call(self):
        """9 evidence items produce exactly ONE batch Gemini call for top 4 items."""
        items = [
            NormalizedEvidence(
                evidence_id=uuid4(),
                url=f"https://source{i}.com/page",
                title=f"Title {i}",
                source_domain=f"source{i}.com",
                source_type=SourceType.NEWS_MEDIA,
                content_snippet=f"Content {i}",
                highlights=[f"h{i}"],
                discovery_query=f"query {i}",
                discovery_query_intent="test_intent",
            )
            for i in range(9)
        ]

        # Prepare mock response for the top 4 items
        mock_client = MagicMock()
        mock_response = MagicMock()
        
        batch_payload = {
            "verifications": [
                {
                    "evidence_id": str(items[i].evidence_id),
                    "merchant_match": "direct_match",
                    "temporal_match": "exact_match",
                    "explanation_support": "strong_explanation",
                    "evidence_strength": "strong_direct",
                    "source_credibility": "high",
                    "event_category": "flash_sale",
                    "key_facts": [f"Fact {i}"],
                    "contradictions_identified": [],
                    "uncertainties_noted": [],
                    "reasoning_summary": f"Verified item {i}",
                }
                for i in range(4)
            ]
        }
        mock_response.text = json.dumps(batch_payload)
        mock_client._client.models.generate_content.return_value = mock_response
        mock_client._model_name = "gemini-3.5-flash-lite"

        verifier = GeminiVerifier(client=mock_client)
        result = verifier.verify_all_evidence(
            investigation_id=uuid4(),
            evidence_items=items,
            merchant_name="UrbanCraft India",
            max_evidence_items=4,
        )

        # Crucial check: Exactly 1 API call made to Gemini (not 9)
        assert mock_client._client.models.generate_content.call_count == 1

        # Total 9 items returned in result
        assert len(result.items) == 9
        verified_items = [item for item in result.items if item.status == VerificationStatus.VERIFIED]
        skipped_items = [item for item in result.items if item.status == VerificationStatus.SKIPPED]

        assert len(verified_items) == 4
        assert len(skipped_items) == 5
        assert all(item.merchant_match == MerchantMatchLevel.DIRECT_MATCH for item in verified_items)
        assert all(item.status == VerificationStatus.SKIPPED for item in skipped_items)

    def test_verify_all_evidence_graceful_failure_on_quota_error(self):
        """When Gemini call fails due to quota or provider error, items are marked FAILED without crashing."""
        items = [
            NormalizedEvidence(
                evidence_id=uuid4(),
                url="https://source1.com/page",
                title="Title 1",
                source_domain="source1.com",
                source_type=SourceType.NEWS_MEDIA,
                content_snippet="Content 1",
                discovery_query="query 1",
                discovery_query_intent="test_intent",
            ),
            NormalizedEvidence(
                evidence_id=uuid4(),
                url="https://source2.com/page",
                title="Title 2",
                source_domain="source2.com",
                source_type=SourceType.GENERAL_WEB,
                content_snippet="Content 2",
                discovery_query="query 2",
                discovery_query_intent="test_intent",
            ),
        ]

        mock_client = MagicMock()
        mock_client._client.models.generate_content.side_effect = Exception("429 ResourceExhausted: GenerateRequestsPerDay quota exceeded")
        mock_client._model_name = "gemini-3.5-flash-lite"

        verifier = GeminiVerifier(client=mock_client)
        result = verifier.verify_all_evidence(
            investigation_id=uuid4(),
            evidence_items=items,
            merchant_name="UrbanCraft India",
            max_evidence_items=1,  # 1 selected, 1 skipped
        )

        assert len(result.items) == 2
        selected_failed = [i for i in result.items if i.status == VerificationStatus.FAILED]
        skipped = [i for i in result.items if i.status == VerificationStatus.SKIPPED]

        assert len(selected_failed) == 1
        assert len(skipped) == 1
        assert "ResourceExhausted" in selected_failed[0].failure_reason
        assert any("Gemini provider error" in u for u in result.overall_uncertainties)

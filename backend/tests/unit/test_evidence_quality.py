"""
Unit tests for Evidence Quality Gates & Annotation Service.

Validates:
- Valid URL gate (detects invalid schemes, missing netloc)
- Source domain gate (detects missing or unknown domains)
- Content availability gate (snippet/highlight presence)
- Near-duplicate claim detection and grouping (evidence_group_id)
- Entity relevance signal (advisory metadata only, does not disqualify)
"""

from uuid import uuid4
import pytest

from app.schemas.evidence import NormalizedEvidence, SourceType
from app.services.evidence_quality import EvidenceQualityService, QualityGateResult


class TestEvidenceQualityService:
    """Tests for individual quality gates and collection annotation."""

    def test_valid_url_gate(self):
        """Should pass valid http/https URLs and fail malformed or missing URLs."""
        valid_ev = NormalizedEvidence(
            url="https://economictimes.indiatimes.com/article/123",
            source_domain="economictimes.indiatimes.com",
            content_snippet="Valid content snippet with enough length for verification.",
            discovery_query="test query",
            discovery_query_intent="timeframe_event",
        )
        invalid_ev = NormalizedEvidence(
            url="ftp://bad-scheme.com/file",
            source_domain="bad-scheme.com",
            content_snippet="Valid content snippet with enough length for verification.",
            discovery_query="test query",
            discovery_query_intent="timeframe_event",
        )

        annotated, summary = EvidenceQualityService.annotate_collection([valid_ev, invalid_ev], "Test Merchant")
        assert annotated[0].is_usable is True
        assert annotated[1].is_usable is False

    def test_source_domain_gate(self):
        """Should fail if source_domain is missing, empty, or 'unknown'."""
        unknown_ev = NormalizedEvidence(
            url="https://some-site.com/test",
            source_domain="unknown",
            content_snippet="Valid content snippet with enough length for verification.",
            discovery_query="test query",
            discovery_query_intent="timeframe_event",
        )
        annotated, summary = EvidenceQualityService.annotate_collection([unknown_ev], "Test Merchant")
        assert annotated[0].is_usable is False
        assert any(g.gate_name == "source_domain_present" and not g.passed for g in annotated[0].annotations)

    def test_content_availability_gate(self):
        """Should fail if snippet and highlights are both empty/too brief."""
        empty_content_ev = NormalizedEvidence(
            url="https://valid-site.com/article",
            source_domain="valid-site.com",
            content_snippet="",
            highlights=[],
            discovery_query="test query",
            discovery_query_intent="timeframe_event",
        )
        annotated, summary = EvidenceQualityService.annotate_collection([empty_content_ev], "Test Merchant")
        assert annotated[0].is_usable is False
        assert any(g.gate_name == "content_availability" and not g.passed for g in annotated[0].annotations)

    def test_near_duplicate_claim_grouping(self):
        """Should detect near-duplicate snippets across domains and assign same claim cluster."""
        shared_text = (
            "UrbanCraft India announced its massive festive artisan discount drive nationwide today. "
            "Customers receive up to 60 percent discounts on all handmade goods."
        )
        item1 = NormalizedEvidence(
            url="https://prnewswire.com/release-1",
            source_domain="prnewswire.com",
            content_snippet=shared_text,
            discovery_query="query 1",
            discovery_query_intent="merchant_announcement",
        )
        item2 = NormalizedEvidence(
            url="https://businesswire.com/release-2",
            source_domain="businesswire.com",
            content_snippet=shared_text,  # Identical claim syndicated
            discovery_query="query 2",
            discovery_query_intent="merchant_announcement",
        )

        annotated, summary = EvidenceQualityService.annotate_collection([item1, item2], "UrbanCraft India")
        assert annotated[0].evidence_group_id == annotated[1].evidence_group_id
        assert summary.unique_claim_groups == 1

        # Second item should have an advisory warning about syndication
        dup_gate = next(g for g in annotated[1].annotations if g.gate_name == "near_duplicate_claim")
        assert dup_gate.is_advisory is True
        assert dup_gate.passed is False
        assert "syndicated" in dup_gate.reason.lower()

    def test_entity_relevance_signal_is_advisory_only(self):
        """
        Critical User Instruction 6: Entity relevance check is an ADVISORY SIGNAL.
        It must NOT disqualify an evidence item from being usable.
        """
        ev_without_exact_name = NormalizedEvidence(
            url="https://techcrunch.com/article",
            source_domain="techcrunch.com",
            title="D2C Artisan Brands See Massive Holiday Surge",
            content_snippet="Multiple handmade goods sellers in India recorded 10x velocity spikes during the festive kickoff.",
            discovery_query="test query",
            discovery_query_intent="timeframe_event",
        )

        annotated, summary = EvidenceQualityService.annotate_collection(
            [ev_without_exact_name],
            merchant_name="UrbanCraft Handlooms Pvt Ltd",
            merchant_domain="urbancraft.in",
        )

        # Usable must remain True despite entity relevance warning
        assert annotated[0].is_usable is True
        rel_gate = next(g for g in annotated[0].annotations if g.gate_name == "entity_relevance_signal")
        assert rel_gate.is_advisory is True
        assert rel_gate.passed is False
        assert "advisory" in rel_gate.reason.lower()

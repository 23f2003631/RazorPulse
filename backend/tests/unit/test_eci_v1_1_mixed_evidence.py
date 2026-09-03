"""
Mixed-Evidence Tests for ECI v1.1.

Mandated by Architectural Review (Item 12):
Verifies that per-item gating mechanisms do NOT leak or interfere across
evidence items in multi-item investigations.

Scenarios:
Mix-A: Valid high-quality source + Unrelated source -> Valid source remains usable; unrelated is excluded.
Mix-B: Valid source + Low-quality social rumor -> Social rumor does NOT globally cap the investigation.
Mix-C: Pre-anomaly source + Post-anomaly source -> Pre-anomaly corroborates; post-anomaly cannot causally corroborate.
Mix-D: Original press release + 3 syndicated copies -> Evaluated as 1 claim group, not 4 independent sources.
Mix-E: Valid source + Ambiguous entity source -> Valid evidence unaffected; ambiguous contributes uncertainty if applicable.
"""

from uuid import uuid4
import pytest

from app.schemas.eci import ECIBand, ECIFactorCategory
from app.schemas.evidence import NormalizedEvidence, SourceType
from app.schemas.verification import (
    EvidenceStrength,
    EvidenceVerificationItem,
    ExplanationSupportLevel,
    MerchantMatchLevel,
    SourceCredibilityLevel,
    TemporalMatchLevel,
    VerificationResult,
    VerificationStatus,
)
from app.services.scoring.eci_engine import ECIEngine


def _ev(domain: str, title: str = "Title") -> NormalizedEvidence:
    return NormalizedEvidence(
        evidence_id=uuid4(),
        url=f"https://{domain}/item-{uuid4().hex[:6]}",
        title=title,
        source_domain=domain,
        source_type=SourceType.NEWS_MEDIA,
        content_snippet=f"Snippet from {domain} about the event.",
        discovery_query="test",
        discovery_query_intent="test",
    )


def _vi(
    ev_id,
    merchant_match=MerchantMatchLevel.DIRECT_MATCH,
    temporal_match=TemporalMatchLevel.EXACT_MATCH,
    explanation_support=ExplanationSupportLevel.STRONG_EXPLANATION,
    evidence_strength=EvidenceStrength.STRONG_DIRECT,
    source_credibility=SourceCredibilityLevel.HIGH,
    contradictions=None,
    uncertainties=None,
) -> EvidenceVerificationItem:
    return EvidenceVerificationItem(
        evidence_id=ev_id,
        status=VerificationStatus.VERIFIED,
        merchant_match=merchant_match,
        temporal_match=temporal_match,
        explanation_support=explanation_support,
        evidence_strength=evidence_strength,
        source_credibility=source_credibility,
        contradictions_identified=contradictions or [],
        uncertainties_noted=uncertainties or [],
        reasoning_summary="Verification summary.",
    )


class TestMixedEvidenceScenarios:
    """Verifies evidence isolation in heterogeneous multi-item investigations."""

    def test_mix_a_valid_plus_unrelated_evidence(self):
        """
        Mix-A: 1 valid high-quality source + 1 unrelated source.
        The valid source must remain usable; the unrelated source must be excluded
        with an audit reason, and must NOT invalidate or reduce the valid source.
        """
        ev_valid = _ev("valid-news.com", "Merchant Annual Mega Sale")
        vi_valid = _vi(
            ev_valid.evidence_id,
            merchant_match=MerchantMatchLevel.DIRECT_MATCH,
            temporal_match=TemporalMatchLevel.EXACT_MATCH,
            explanation_support=ExplanationSupportLevel.STRONG_EXPLANATION,
            evidence_strength=EvidenceStrength.STRONG_DIRECT,
            source_credibility=SourceCredibilityLevel.HIGH,
        )

        ev_unrelated = _ev("unrelated-news.com", "Completely Different Company Sale")
        vi_unrelated = _vi(
            ev_unrelated.evidence_id,
            merchant_match=MerchantMatchLevel.UNRELATED,
            temporal_match=TemporalMatchLevel.EXACT_MATCH,  # Same date, but wrong company
            explanation_support=ExplanationSupportLevel.STRONG_EXPLANATION,
            evidence_strength=EvidenceStrength.STRONG_DIRECT,
            source_credibility=SourceCredibilityLevel.HIGH,
        )

        vr = VerificationResult(
            investigation_id=uuid4(),
            items=[vi_valid, vi_unrelated],
            overall_contradictions=[],
            overall_uncertainties=[],
            verified_at_timestamp="now",
        )

        res = ECIEngine.calculate_eci(vr, [ev_valid, ev_unrelated])

        # 1 eligible, 1 excluded
        assert res.eligible_evidence_count == 1
        assert len(res.excluded_items) == 1
        assert res.excluded_items[0].evidence_id == ev_unrelated.evidence_id
        assert res.excluded_items[0].exclusion_reason == "entity_mismatch"

        # The valid source alone scores 90 (25 entity + 25 temporal + 20 support + 20 source)
        assert res.eci_score == 90
        assert res.band == ECIBand.VERY_STRONG

        # Entity match factor uses the valid item
        entity_factor = next(f for f in res.factors if f.category == ECIFactorCategory.ENTITY_MATCH)
        assert entity_factor.points_awarded == 25.0
        assert entity_factor.evidence_ids == [ev_valid.evidence_id]

    def test_mix_b_valid_plus_low_quality_social(self):
        """
        Mix-B: 1 valid high-quality source + 1 low-quality social rumor.
        The low-quality social rumor must NOT globally cap the investigation at 29.
        The valid source should maintain strong corroboration.
        """
        ev_official = _ev("indiatoday.in", "Official festive sale launch")
        vi_official = _vi(
            ev_official.evidence_id,
            merchant_match=MerchantMatchLevel.DIRECT_MATCH,
            temporal_match=TemporalMatchLevel.EXACT_MATCH,
            explanation_support=ExplanationSupportLevel.STRONG_EXPLANATION,
            evidence_strength=EvidenceStrength.STRONG_DIRECT,
            source_credibility=SourceCredibilityLevel.HIGH,
        )

        ev_social = _ev("reddit.com", "Unverified rumor on reddit")
        vi_social = _vi(
            ev_social.evidence_id,
            merchant_match=MerchantMatchLevel.DIRECT_MATCH,
            temporal_match=TemporalMatchLevel.EXACT_MATCH,
            explanation_support=ExplanationSupportLevel.WEAK_EXPLANATION,
            evidence_strength=EvidenceStrength.WEAK_CIRCUMSTANTIAL,
            source_credibility=SourceCredibilityLevel.LOW,
        )

        vr = VerificationResult(
            investigation_id=uuid4(),
            items=[vi_official, vi_social],
            overall_contradictions=[],
            overall_uncertainties=[],
            verified_at_timestamp="now",
        )

        res = ECIEngine.calculate_eci(vr, [ev_official, ev_social])

        # Both are eligible (social is valid entity/timing, just weak authority)
        assert res.eligible_evidence_count == 2
        # Investigation is NOT capped at 29 because ev_official has HIGH credibility (ceiling = 100)
        assert res.eci_score >= 80
        assert res.band in (ECIBand.STRONG, ECIBand.VERY_STRONG)

    def test_mix_c_pre_anomaly_plus_post_anomaly(self):
        """
        Mix-C: 1 pre/during-anomaly source + 1 post-anomaly source.
        The pre-anomaly source provides causal explanation; the post-anomaly
        source has its explanation support zeroed out and cannot cause inflation.
        """
        ev_during = _ev("ndtv.com", "Midnight flash sale announced")
        vi_during = _vi(
            ev_during.evidence_id,
            merchant_match=MerchantMatchLevel.DIRECT_MATCH,
            temporal_match=TemporalMatchLevel.EXACT_MATCH,
            explanation_support=ExplanationSupportLevel.STRONG_EXPLANATION,
            evidence_strength=EvidenceStrength.STRONG_DIRECT,
            source_credibility=SourceCredibilityLevel.HIGH,
        )

        ev_post = _ev("blog.com", "Post-event review 3 weeks later")
        vi_post = _vi(
            ev_post.evidence_id,
            merchant_match=MerchantMatchLevel.DIRECT_MATCH,
            temporal_match=TemporalMatchLevel.POST_ANOMALY,
            explanation_support=ExplanationSupportLevel.STRONG_EXPLANATION,  # Would be strong, but is post-anomaly
            evidence_strength=EvidenceStrength.STRONG_DIRECT,
            source_credibility=SourceCredibilityLevel.HIGH,
        )

        vr = VerificationResult(
            investigation_id=uuid4(),
            items=[vi_during, vi_post],
            overall_contradictions=[],
            overall_uncertainties=[],
            verified_at_timestamp="now",
        )

        res = ECIEngine.calculate_eci(vr, [ev_during, ev_post])

        # Both are eligible, but ev_during provides the causal explanation
        expl_factor = next(f for f in res.factors if f.category == ECIFactorCategory.EXPLANATION_SUPPORT)
        assert expl_factor.points_awarded == 20.0
        # Attributed to the causally-eligible item
        assert expl_factor.evidence_ids == [ev_during.evidence_id]

    def test_mix_d_original_plus_syndicated_copies(self):
        """
        Mix-D: 1 original press release + 3 syndicated copies across distinct domains.
        Should be evaluated as 1 claim group, yielding 0 independence bonus despite 4 domains.
        """
        ev_orig = _ev("prnewswire.com", "Company launches product X")
        ev_syn1 = _ev("businesswire.com", "Company launches product X")
        ev_syn2 = _ev("techportal.com", "Company launches product X")
        ev_syn3 = _ev("financenews.com", "Company launches product X")

        items = [ev_orig, ev_syn1, ev_syn2, ev_syn3]
        vis = [
            _vi(
                ev.evidence_id,
                merchant_match=MerchantMatchLevel.DIRECT_MATCH,
                temporal_match=TemporalMatchLevel.EXACT_MATCH,
                explanation_support=ExplanationSupportLevel.MODERATE_EXPLANATION,
                evidence_strength=EvidenceStrength.MODERATE_INDIRECT,
                source_credibility=SourceCredibilityLevel.MEDIUM,
            )
            for ev in items
        ]

        vr = VerificationResult(
            investigation_id=uuid4(),
            items=vis,
            overall_contradictions=[],
            overall_uncertainties=[],
            verified_at_timestamp="now",
        )

        # All 4 share the same claim group ID
        claim_groups = {ev.evidence_id: "syndicated_claim_alpha" for ev in items}

        res = ECIEngine.calculate_eci(vr, items, evidence_group_ids=claim_groups)

        # 4 items, but only 1 unique claim group
        indep_factor = next(f for f in res.factors if f.category == ECIFactorCategory.INDEPENDENT_CORROBORATION)
        assert indep_factor.points_awarded == 0.0
        assert "1_independent_claim_groups" in indep_factor.raw_value

    def test_mix_e_valid_plus_ambiguous_entity(self):
        """
        Mix-E: 1 valid confirmed source + 1 ambiguous entity source.
        Valid evidence provides direct match (25 pts); ambiguous source does not
        reduce or override the confirmed match.
        """
        ev_confirmed = _ev("reuters.com", "Acme Retail confirms festival sale")
        vi_confirmed = _vi(
            ev_confirmed.evidence_id,
            merchant_match=MerchantMatchLevel.DIRECT_MATCH,
            temporal_match=TemporalMatchLevel.EXACT_MATCH,
            explanation_support=ExplanationSupportLevel.STRONG_EXPLANATION,
            evidence_strength=EvidenceStrength.STRONG_DIRECT,
            source_credibility=SourceCredibilityLevel.HIGH,
        )

        ev_ambiguous = _ev("localforum.in", "Someone said Acme might be on sale")
        vi_ambiguous = _vi(
            ev_ambiguous.evidence_id,
            merchant_match=MerchantMatchLevel.UNCERTAIN,
            temporal_match=TemporalMatchLevel.EXACT_MATCH,
            explanation_support=ExplanationSupportLevel.WEAK_EXPLANATION,
            evidence_strength=EvidenceStrength.WEAK_CIRCUMSTANTIAL,
            source_credibility=SourceCredibilityLevel.LOW,
            uncertainties=["Entity mention is vague"],
        )

        vr = VerificationResult(
            investigation_id=uuid4(),
            items=[vi_confirmed, vi_ambiguous],
            overall_contradictions=[],
            overall_uncertainties=[],
            verified_at_timestamp="now",
        )

        res = ECIEngine.calculate_eci(vr, [ev_confirmed, ev_ambiguous])

        # Entity match evaluates to DIRECT_MATCH (25) from the confirmed source
        entity_factor = next(f for f in res.factors if f.category == ECIFactorCategory.ENTITY_MATCH)
        assert entity_factor.points_awarded == 25.0
        assert entity_factor.raw_value == "direct_match"
        assert res.eci_score >= 80

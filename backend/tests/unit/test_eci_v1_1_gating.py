"""
Unit Tests for ECI v1.1 Gating Rules (Isolated Evaluation).

Tests each gating mechanism in isolation:
1. Per-item Entity Gating (UNRELATED -> contribution 0, recorded in excluded_items)
2. Per-item Temporal Gating (POST_ANOMALY / UNRELATED_TIMING -> explanation 0)
3. Source Authority Ceiling (LOW / WEAK / UNKNOWN capped at 29, CONTRADICTED capped at 0)
4. Claim-Group Independence (Syndicated claims share group -> 0 bonus; distinct groups get bonus)
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


def _create_ev(domain: str = "example.com") -> NormalizedEvidence:
    return NormalizedEvidence(
        evidence_id=uuid4(),
        url=f"https://{domain}/article-{uuid4().hex[:6]}",
        source_domain=domain,
        source_type=SourceType.NEWS_MEDIA,
        content_snippet="Test evidence content snippet for verification.",
        discovery_query="test query",
        discovery_query_intent="timeframe_event",
    )


def _create_vi(
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
        reasoning_summary="Verification reasoning.",
    )


# =============================================================================
# 1. Entity Gating Tests
# =============================================================================

class TestEntityGating:
    """Verify entity match gating rules in isolation."""

    def test_unrelated_entity_produces_zero_eci_and_audit_exclusion(self):
        """UNRELATED entity item must be excluded with audit trail and produce ECI=0."""
        ev = _create_ev()
        vi = _create_vi(ev.evidence_id, merchant_match=MerchantMatchLevel.UNRELATED)
        vr = VerificationResult(
            investigation_id=uuid4(),
            items=[vi],
            overall_contradictions=[],
            overall_uncertainties=[],
            verified_at_timestamp="now",
        )

        res = ECIEngine.calculate_eci(vr, [ev])

        assert res.eci_score == 0
        assert res.band == ECIBand.LOW
        assert res.eligible_evidence_count == 0
        assert len(res.excluded_items) == 1
        assert res.excluded_items[0].evidence_id == ev.evidence_id
        assert res.excluded_items[0].exclusion_reason == "entity_mismatch"
        assert res.excluded_items[0].raw_contribution > 0.0  # Had raw points before gating
        assert res.positive_points == 0.0

    def test_direct_match_entity_is_eligible_without_exclusion(self):
        """DIRECT_MATCH entity must receive 25 pts and not be excluded."""
        ev = _create_ev()
        vi = _create_vi(ev.evidence_id, merchant_match=MerchantMatchLevel.DIRECT_MATCH)
        vr = VerificationResult(
            investigation_id=uuid4(),
            items=[vi],
            overall_contradictions=[],
            overall_uncertainties=[],
            verified_at_timestamp="now",
        )

        res = ECIEngine.calculate_eci(vr, [ev])

        assert res.eligible_evidence_count == 1
        assert len(res.excluded_items) == 0
        entity_factor = next(f for f in res.factors if f.category == ECIFactorCategory.ENTITY_MATCH)
        assert entity_factor.points_awarded == 25.0

    def test_related_entity_is_eligible_with_reduced_points(self):
        """RELATED_ENTITY must be eligible and receive 12 pts."""
        ev = _create_ev()
        vi = _create_vi(ev.evidence_id, merchant_match=MerchantMatchLevel.RELATED_ENTITY)
        vr = VerificationResult(
            investigation_id=uuid4(),
            items=[vi],
            overall_contradictions=[],
            overall_uncertainties=[],
            verified_at_timestamp="now",
        )

        res = ECIEngine.calculate_eci(vr, [ev])

        assert res.eligible_evidence_count == 1
        assert len(res.excluded_items) == 0
        entity_factor = next(f for f in res.factors if f.category == ECIFactorCategory.ENTITY_MATCH)
        assert entity_factor.points_awarded == 12.0

    def test_uncertain_entity_is_eligible_with_reduced_points(self):
        """UNCERTAIN entity must be eligible and receive 5 pts."""
        ev = _create_ev()
        vi = _create_vi(ev.evidence_id, merchant_match=MerchantMatchLevel.UNCERTAIN)
        vr = VerificationResult(
            investigation_id=uuid4(),
            items=[vi],
            overall_contradictions=[],
            overall_uncertainties=[],
            verified_at_timestamp="now",
        )

        res = ECIEngine.calculate_eci(vr, [ev])

        assert res.eligible_evidence_count == 1
        entity_factor = next(f for f in res.factors if f.category == ECIFactorCategory.ENTITY_MATCH)
        assert entity_factor.points_awarded == 5.0


# =============================================================================
# 2. Temporal Gating Tests
# =============================================================================

class TestTemporalGating:
    """Verify temporal causality gating rules in isolation."""

    def test_post_anomaly_zeros_explanation_support(self):
        """POST_ANOMALY item cannot provide causal explanation support (pts = 0)."""
        ev = _create_ev()
        vi = _create_vi(
            ev.evidence_id,
            temporal_match=TemporalMatchLevel.POST_ANOMALY,
            explanation_support=ExplanationSupportLevel.STRONG_EXPLANATION,
        )
        vr = VerificationResult(
            investigation_id=uuid4(),
            items=[vi],
            overall_contradictions=[],
            overall_uncertainties=[],
            verified_at_timestamp="now",
        )

        res = ECIEngine.calculate_eci(vr, [ev])

        # Entity match (25) + Temporal match (0) + Explanation (0, gated) + Source (20) = 45
        expl_factor = next(f for f in res.factors if f.category == ECIFactorCategory.EXPLANATION_SUPPORT)
        assert expl_factor.points_awarded == 0.0
        assert "post-anomaly" in expl_factor.explanation.lower() or "post" in expl_factor.explanation.lower()

    def test_unrelated_timing_zeros_explanation_support(self):
        """UNRELATED_TIMING item cannot provide causal explanation support."""
        ev = _create_ev()
        vi = _create_vi(
            ev.evidence_id,
            temporal_match=TemporalMatchLevel.UNRELATED_TIMING,
            explanation_support=ExplanationSupportLevel.STRONG_EXPLANATION,
        )
        vr = VerificationResult(
            investigation_id=uuid4(),
            items=[vi],
            overall_contradictions=[],
            overall_uncertainties=[],
            verified_at_timestamp="now",
        )

        res = ECIEngine.calculate_eci(vr, [ev])

        expl_factor = next(f for f in res.factors if f.category == ECIFactorCategory.EXPLANATION_SUPPORT)
        assert expl_factor.points_awarded == 0.0

    def test_exact_match_allows_full_explanation_support(self):
        """EXACT_MATCH item receives full temporal (25) and full explanation (20)."""
        ev = _create_ev()
        vi = _create_vi(
            ev.evidence_id,
            temporal_match=TemporalMatchLevel.EXACT_MATCH,
            explanation_support=ExplanationSupportLevel.STRONG_EXPLANATION,
        )
        vr = VerificationResult(
            investigation_id=uuid4(),
            items=[vi],
            overall_contradictions=[],
            overall_uncertainties=[],
            verified_at_timestamp="now",
        )

        res = ECIEngine.calculate_eci(vr, [ev])

        timing_factor = next(f for f in res.factors if f.category == ECIFactorCategory.TEMPORAL_ALIGNMENT)
        expl_factor = next(f for f in res.factors if f.category == ECIFactorCategory.EXPLANATION_SUPPORT)
        assert timing_factor.points_awarded == 25.0
        assert expl_factor.points_awarded == 20.0

    def test_window_match_allows_full_explanation_support(self):
        """WINDOW_MATCH item receives window temporal (18) and full explanation (20)."""
        ev = _create_ev()
        vi = _create_vi(
            ev.evidence_id,
            temporal_match=TemporalMatchLevel.WINDOW_MATCH,
            explanation_support=ExplanationSupportLevel.STRONG_EXPLANATION,
        )
        vr = VerificationResult(
            investigation_id=uuid4(),
            items=[vi],
            overall_contradictions=[],
            overall_uncertainties=[],
            verified_at_timestamp="now",
        )

        res = ECIEngine.calculate_eci(vr, [ev])

        timing_factor = next(f for f in res.factors if f.category == ECIFactorCategory.TEMPORAL_ALIGNMENT)
        expl_factor = next(f for f in res.factors if f.category == ECIFactorCategory.EXPLANATION_SUPPORT)
        assert timing_factor.points_awarded == 18.0
        assert expl_factor.points_awarded == 20.0


# =============================================================================
# 3. Source Authority Ceiling Tests
# =============================================================================

class TestSourceAuthorityCeiling:
    """Verify source authority ceilings cap low-quality evidence at 29."""

    def test_low_credibility_capped_at_29(self):
        """Single LOW credibility item cannot exceed 29 ECI despite exact entity and timing."""
        ev = _create_ev("reddit.com")
        vi = _create_vi(
            ev.evidence_id,
            merchant_match=MerchantMatchLevel.DIRECT_MATCH,
            temporal_match=TemporalMatchLevel.EXACT_MATCH,
            explanation_support=ExplanationSupportLevel.STRONG_EXPLANATION,
            evidence_strength=EvidenceStrength.WEAK_CIRCUMSTANTIAL,
            source_credibility=SourceCredibilityLevel.LOW,
        )
        vr = VerificationResult(
            investigation_id=uuid4(),
            items=[vi],
            overall_contradictions=[],
            overall_uncertainties=[],
            verified_at_timestamp="now",
        )

        res = ECIEngine.calculate_eci(vr, [ev])

        # Raw points would be 25 + 25 + 20 + 5 = 75 (STRONG)
        # Capped at 29 -> Band LOW
        assert res.eci_score <= 29
        assert res.band == ECIBand.LOW
        assert res.positive_points == 29.0
        assert any(f.factor_id == "ceiling_authority_cap" for f in res.factors)

    def test_high_credibility_strong_direct_not_capped_at_29(self):
        """HIGH credibility + STRONG_DIRECT evidence is not capped at 29."""
        ev = _create_ev("reuters.com")
        vi = _create_vi(
            ev.evidence_id,
            merchant_match=MerchantMatchLevel.DIRECT_MATCH,
            temporal_match=TemporalMatchLevel.EXACT_MATCH,
            explanation_support=ExplanationSupportLevel.STRONG_EXPLANATION,
            evidence_strength=EvidenceStrength.STRONG_DIRECT,
            source_credibility=SourceCredibilityLevel.HIGH,
        )
        vr = VerificationResult(
            investigation_id=uuid4(),
            items=[vi],
            overall_contradictions=[],
            overall_uncertainties=[],
            verified_at_timestamp="now",
        )

        res = ECIEngine.calculate_eci(vr, [ev])

        assert res.eci_score == 90
        assert res.band == ECIBand.VERY_STRONG

    def test_unknown_credibility_capped_at_29(self):
        """UNKNOWN source credibility is capped at 29."""
        ev = _create_ev("unverified-blog.xyz")
        vi = _create_vi(
            ev.evidence_id,
            merchant_match=MerchantMatchLevel.DIRECT_MATCH,
            temporal_match=TemporalMatchLevel.EXACT_MATCH,
            explanation_support=ExplanationSupportLevel.STRONG_EXPLANATION,
            evidence_strength=EvidenceStrength.WEAK_CIRCUMSTANTIAL,
            source_credibility=SourceCredibilityLevel.UNKNOWN,
        )
        vr = VerificationResult(
            investigation_id=uuid4(),
            items=[vi],
            overall_contradictions=[],
            overall_uncertainties=[],
            verified_at_timestamp="now",
        )

        res = ECIEngine.calculate_eci(vr, [ev])

        assert res.eci_score <= 29
        assert res.band == ECIBand.LOW

    def test_contradicted_evidence_ceiling_is_zero(self):
        """CONTRADICTED evidence strength ceiling is 0."""
        ev = _create_ev()
        vi = _create_vi(
            ev.evidence_id,
            evidence_strength=EvidenceStrength.CONTRADICTED,
            source_credibility=SourceCredibilityLevel.HIGH,
        )
        vr = VerificationResult(
            investigation_id=uuid4(),
            items=[vi],
            overall_contradictions=["Source refutes sale"],
            overall_uncertainties=[],
            verified_at_timestamp="now",
        )

        res = ECIEngine.calculate_eci(vr, [ev])

        assert res.eci_score == 0


# =============================================================================
# 4. Claim-Group Independence Tests
# =============================================================================

class TestClaimGroupIndependence:
    """Verify claim-group aware independent corroboration bonus."""

    def test_three_distinct_claim_groups_earn_10_bonus(self):
        """3 items with distinct claim groups receive +10 independence bonus."""
        ev1, ev2, ev3 = _create_ev("d1.com"), _create_ev("d2.com"), _create_ev("d3.com")
        vi1 = _create_vi(ev1.evidence_id)
        vi2 = _create_vi(ev2.evidence_id)
        vi3 = _create_vi(ev3.evidence_id)
        vr = VerificationResult(
            investigation_id=uuid4(),
            items=[vi1, vi2, vi3],
            overall_contradictions=[],
            overall_uncertainties=[],
            verified_at_timestamp="now",
        )
        groups = {
            ev1.evidence_id: "group_alpha",
            ev2.evidence_id: "group_beta",
            ev3.evidence_id: "group_gamma",
        }

        res = ECIEngine.calculate_eci(vr, [ev1, ev2, ev3], evidence_group_ids=groups)

        indep = next(f for f in res.factors if f.category == ECIFactorCategory.INDEPENDENT_CORROBORATION)
        assert indep.points_awarded == 10.0
        assert res.eci_score == 100

    def test_syndicated_claims_sharing_same_group_receive_zero_bonus(self):
        """3 items from different domains sharing the same claim group receive 0 independence bonus."""
        ev1, ev2, ev3 = _create_ev("d1.com"), _create_ev("d2.com"), _create_ev("d3.com")
        vi1 = _create_vi(ev1.evidence_id)
        vi2 = _create_vi(ev2.evidence_id)
        vi3 = _create_vi(ev3.evidence_id)
        vr = VerificationResult(
            investigation_id=uuid4(),
            items=[vi1, vi2, vi3],
            overall_contradictions=[],
            overall_uncertainties=[],
            verified_at_timestamp="now",
        )
        # All 3 belong to the SAME claim group (syndicated press release)
        same_group = {
            ev1.evidence_id: "syndicated_pr_001",
            ev2.evidence_id: "syndicated_pr_001",
            ev3.evidence_id: "syndicated_pr_001",
        }

        res = ECIEngine.calculate_eci(vr, [ev1, ev2, ev3], evidence_group_ids=same_group)

        indep = next(f for f in res.factors if f.category == ECIFactorCategory.INDEPENDENT_CORROBORATION)
        assert indep.points_awarded == 0.0
        assert "single claim group" in indep.explanation.lower()

    def test_two_distinct_claim_groups_earn_5_bonus(self):
        """2 items with distinct claim groups receive +5 independence bonus."""
        ev1, ev2 = _create_ev("d1.com"), _create_ev("d2.com")
        vi1 = _create_vi(ev1.evidence_id)
        vi2 = _create_vi(ev2.evidence_id)
        vr = VerificationResult(
            investigation_id=uuid4(),
            items=[vi1, vi2],
            overall_contradictions=[],
            overall_uncertainties=[],
            verified_at_timestamp="now",
        )
        groups = {
            ev1.evidence_id: "group_a",
            ev2.evidence_id: "group_b",
        }

        res = ECIEngine.calculate_eci(vr, [ev1, ev2], evidence_group_ids=groups)

        indep = next(f for f in res.factors if f.category == ECIFactorCategory.INDEPENDENT_CORROBORATION)
        assert indep.points_awarded == 5.0
        assert res.eci_score == 95

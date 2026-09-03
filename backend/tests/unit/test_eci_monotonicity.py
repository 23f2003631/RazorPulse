"""
Deterministic ECI Monotonicity & Directional Invariant Tests.

CRITICAL USER REQUIREMENT (Instruction 12):
Evaluates expected directional behavior of the ECI scoring engine:
1. Temporal alignment monotonicity: more aligned timing -> ECI does not decrease.
2. Entity match monotonicity: stronger entity match -> ECI does not decrease.
3. Independent corroboration monotonicity: adding distinct credible domains -> ECI does not decrease.
4. Contradiction penalty monotonicity: introducing contradictions -> ECI does not increase.
5. Duplication resistance: duplicating existing evidence -> ECI does not materially inflate.
6. Unrelated evidence resistance: adding unrelated evidence -> ECI does not increase.
"""

from uuid import uuid4
import pytest

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


def _make_evidence(domain="example.com") -> NormalizedEvidence:
    return NormalizedEvidence(
        evidence_id=uuid4(),
        url=f"https://{domain}/article-{uuid4().hex[:6]}",
        source_domain=domain,
        source_type=SourceType.NEWS_MEDIA,
        content_snippet="Evidence snippet text with details.",
        discovery_query="test",
        discovery_query_intent="timeframe_event",
    )


def _make_verification(
    ev_id,
    merchant_match=MerchantMatchLevel.DIRECT_MATCH,
    temporal_match=TemporalMatchLevel.EXACT_MATCH,
    explanation=ExplanationSupportLevel.STRONG_EXPLANATION,
    strength=EvidenceStrength.STRONG_DIRECT,
    credibility=SourceCredibilityLevel.HIGH,
    contradictions=None,
    uncertainties=None,
) -> EvidenceVerificationItem:
    return EvidenceVerificationItem(
        evidence_id=ev_id,
        status=VerificationStatus.VERIFIED,
        merchant_match=merchant_match,
        temporal_match=temporal_match,
        explanation_support=explanation,
        evidence_strength=strength,
        source_credibility=credibility,
        contradictions_identified=contradictions or [],
        uncertainties_noted=uncertainties or [],
        reasoning_summary="Verification assessment.",
    )


class TestECIMonotonicity:
    """Evaluates mathematical directional invariants of ECI calculation."""

    def test_temporal_alignment_monotonicity(self):
        """If evidence becomes more temporally aligned, ECI must NOT decrease."""
        temporal_levels_ascending = [
            TemporalMatchLevel.UNRELATED_TIMING,
            TemporalMatchLevel.HISTORICAL_PREVIOUS,
            TemporalMatchLevel.WINDOW_MATCH,
            TemporalMatchLevel.EXACT_MATCH,
        ]

        scores = []
        for t_match in temporal_levels_ascending:
            ev = _make_evidence()
            vi = _make_verification(ev.evidence_id, temporal_match=t_match)
            vr = VerificationResult(
                investigation_id=uuid4(),
                items=[vi],
                overall_contradictions=[],
                overall_uncertainties=[],
                verified_at_timestamp="2026-09-01T00:00:00Z",
            )
            result = ECIEngine.calculate_eci(vr, [ev])
            scores.append(result.eci_score)

        # Non-decreasing sequence
        for i in range(len(scores) - 1):
            assert scores[i] <= scores[i + 1], f"Temporal monotonicity violated: {scores[i]} > {scores[i+1]}"

    def test_entity_match_monotonicity(self):
        """If entity match becomes stronger, Factor points and ECI must NOT decrease."""
        entity_levels_ascending = [
            MerchantMatchLevel.UNRELATED,
            MerchantMatchLevel.UNCERTAIN,
            MerchantMatchLevel.RELATED_ENTITY,
            MerchantMatchLevel.DIRECT_MATCH,
        ]

        # 1. Direct factor evaluation points must be strictly non-decreasing
        factor_points = [ECIEngine._eval_entity_match(m)[0] for m in entity_levels_ascending]
        for i in range(len(factor_points) - 1):
            assert factor_points[i] <= factor_points[i + 1], f"Entity factor points non-monotonic: {factor_points}"

        # 2. End-to-end ECI must be non-decreasing across qualifying entity match levels
        # (UNCERTAIN -> RELATED_ENTITY -> DIRECT_MATCH)
        qualifying_levels = [
            MerchantMatchLevel.UNCERTAIN,
            MerchantMatchLevel.RELATED_ENTITY,
            MerchantMatchLevel.DIRECT_MATCH,
        ]
        scores = []
        for e_match in qualifying_levels:
            ev = _make_evidence()
            vi = _make_verification(ev.evidence_id, merchant_match=e_match)
            vr = VerificationResult(
                investigation_id=uuid4(),
                items=[vi],
                overall_contradictions=[],
                overall_uncertainties=[],
                verified_at_timestamp="2026-09-01T00:00:00Z",
            )
            result = ECIEngine.calculate_eci(vr, [ev])
            scores.append(result.eci_score)

        for i in range(len(scores) - 1):
            assert scores[i] <= scores[i + 1], f"Entity match monotonicity violated: {scores[i]} > {scores[i+1]}"

    def test_independent_corroboration_monotonicity(self):
        """Adding credible evidence from new independent domains must NOT decrease ECI."""
        # 1 domain
        ev1 = _make_evidence("domain-a.com")
        vi1 = _make_verification(ev1.evidence_id)
        vr1 = VerificationResult(investigation_id=uuid4(), items=[vi1], overall_contradictions=[], overall_uncertainties=[], verified_at_timestamp="2026-09-01T00:00:00Z")
        res1 = ECIEngine.calculate_eci(vr1, [ev1])

        # 2 distinct domains
        ev2 = _make_evidence("domain-b.com")
        vi2 = _make_verification(ev2.evidence_id)
        vr2 = VerificationResult(investigation_id=uuid4(), items=[vi1, vi2], overall_contradictions=[], overall_uncertainties=[], verified_at_timestamp="2026-09-01T00:00:00Z")
        res2 = ECIEngine.calculate_eci(vr2, [ev1, ev2])

        # 3 distinct domains
        ev3 = _make_evidence("domain-c.com")
        vi3 = _make_verification(ev3.evidence_id)
        vr3 = VerificationResult(investigation_id=uuid4(), items=[vi1, vi2, vi3], overall_contradictions=[], overall_uncertainties=[], verified_at_timestamp="2026-09-01T00:00:00Z")
        res3 = ECIEngine.calculate_eci(vr3, [ev1, ev2, ev3])

        assert res1.eci_score <= res2.eci_score <= res3.eci_score
        assert res3.eci_score > res1.eci_score  # Independent corroboration should boost score

    def test_contradiction_penalty_monotonicity(self):
        """Introducing contradictions must NOT increase ECI."""
        ev = _make_evidence()
        vi = _make_verification(ev.evidence_id)

        # Baseline with no contradictions
        vr_clean = VerificationResult(investigation_id=uuid4(), items=[vi], overall_contradictions=[], overall_uncertainties=[], verified_at_timestamp="2026-09-01T00:00:00Z")
        res_clean = ECIEngine.calculate_eci(vr_clean, [ev])

        # 1 contradiction
        vr_minor = VerificationResult(investigation_id=uuid4(), items=[vi], overall_contradictions=["Minor discrepancy"], overall_uncertainties=[], verified_at_timestamp="2026-09-01T00:00:00Z")
        res_minor = ECIEngine.calculate_eci(vr_minor, [ev])

        # 2 contradictions (severe)
        vr_severe = VerificationResult(investigation_id=uuid4(), items=[vi], overall_contradictions=["Discrepancy 1", "Discrepancy 2"], overall_uncertainties=[], verified_at_timestamp="2026-09-01T00:00:00Z")
        res_severe = ECIEngine.calculate_eci(vr_severe, [ev])

        assert res_clean.eci_score >= res_minor.eci_score >= res_severe.eci_score
        assert res_clean.eci_score > res_minor.eci_score

    def test_duplication_resistance_same_domain(self):
        """Duplicating evidence from the SAME domain must NOT inflate independent corroboration bonus."""
        ev1 = _make_evidence("same-domain.com")
        vi1 = _make_verification(ev1.evidence_id)

        vr1 = VerificationResult(investigation_id=uuid4(), items=[vi1], overall_contradictions=[], overall_uncertainties=[], verified_at_timestamp="2026-09-01T00:00:00Z")
        res1 = ECIEngine.calculate_eci(vr1, [ev1])

        # Add 3 more items from the exact same domain
        ev2 = _make_evidence("same-domain.com")
        vi2 = _make_verification(ev2.evidence_id)
        ev3 = _make_evidence("same-domain.com")
        vi3 = _make_verification(ev3.evidence_id)

        vr_dup = VerificationResult(investigation_id=uuid4(), items=[vi1, vi2, vi3], overall_contradictions=[], overall_uncertainties=[], verified_at_timestamp="2026-09-01T00:00:00Z")
        res_dup = ECIEngine.calculate_eci(vr_dup, [ev1, ev2, ev3])

        # Score must not increase solely due to duplicate domain repetition
        # (Independent corroboration factor must be 0 for single domain)
        corrob_factor = next(f for f in res_dup.factors if f.category.value == "independent_corroboration")
        assert corrob_factor.points_awarded == 0.0
        assert res_dup.eci_score == res1.eci_score

    def test_unrelated_evidence_does_not_increase_eci(self):
        """Adding unrelated / zero-explanation evidence must NOT increase ECI."""
        ev_good = _make_evidence("good-domain.com")
        vi_good = _make_verification(ev_good.evidence_id)

        vr_good = VerificationResult(investigation_id=uuid4(), items=[vi_good], overall_contradictions=[], overall_uncertainties=[], verified_at_timestamp="2026-09-01T00:00:00Z")
        res_good = ECIEngine.calculate_eci(vr_good, [ev_good])

        # Add completely unrelated item
        ev_unrelated = _make_evidence("random-blog.com")
        vi_unrelated = _make_verification(
            ev_unrelated.evidence_id,
            merchant_match=MerchantMatchLevel.UNRELATED,
            explanation=ExplanationSupportLevel.NO_EXPLANATION,
            temporal_match=TemporalMatchLevel.UNRELATED_TIMING,
        )

        vr_mixed = VerificationResult(investigation_id=uuid4(), items=[vi_good, vi_unrelated], overall_contradictions=[], overall_uncertainties=[], verified_at_timestamp="2026-09-01T00:00:00Z")
        res_mixed = ECIEngine.calculate_eci(vr_mixed, [ev_good, ev_unrelated])

        # Adding unrelated evidence must not increase score
        assert res_mixed.eci_score <= res_good.eci_score

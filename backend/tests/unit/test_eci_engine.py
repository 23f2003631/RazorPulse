"""
Unit tests and Deterministic Score Invariant tests for the ECI v1 Heuristic Engine.
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
)
from app.services.scoring.eci_engine import ECIEngine
from tests.fixtures.synthetic_scenarios import (
    SCENARIO_1_EVIDENCE_ITEMS,
    SCENARIO_1_VERIFICATIONS,
    SCENARIO_2_EVIDENCE_ITEMS,
    SCENARIO_2_VERIFICATIONS,
    SCENARIO_3_EVIDENCE_ITEMS,
    SCENARIO_3_VERIFICATIONS,
)


class TestECIEngineScoreInvariants:
    """
    Test suite verifying the 10 core mathematical and behavioral invariants of ECI v1.
    """

    # --- Invariant 1: Reproducibility ---
    def test_invariant_1_reproducibility(self):
        """Same verified evidence inputs must always produce the exact same ECI score and factor breakdown."""
        v_res = VerificationResult(
            investigation_id=uuid4(),
            items=SCENARIO_1_VERIFICATIONS,
            overall_contradictions=[],
            overall_uncertainties=[],
            verified_at_timestamp="2026-08-28T15:00:00Z",
        )

        res1 = ECIEngine.calculate_eci(v_res, SCENARIO_1_EVIDENCE_ITEMS)
        res2 = ECIEngine.calculate_eci(v_res, SCENARIO_1_EVIDENCE_ITEMS)

        assert res1.eci_score == res2.eci_score
        assert res1.band == res2.band
        assert res1.positive_points == res2.positive_points
        assert res1.penalty_points == res2.penalty_points
        assert len(res1.factors) == len(res2.factors)

    # --- Invariant 2: Boundedness [0, 100] ---
    def test_invariant_2_boundedness(self):
        """Score must always remain within [0, 100] even with extreme inputs."""
        # Max positive item
        perfect_item = EvidenceVerificationItem(
            evidence_id=uuid4(),
            merchant_match=MerchantMatchLevel.DIRECT_MATCH,
            temporal_match=TemporalMatchLevel.EXACT_MATCH,
            explanation_support=ExplanationSupportLevel.STRONG_EXPLANATION,
            evidence_strength=EvidenceStrength.STRONG_DIRECT,
            source_credibility=SourceCredibilityLevel.HIGH,
            event_category="sale",
            key_facts=["Confirmed"],
            contradictions_identified=[],
            uncertainties_noted=[],
            reasoning_summary="Perfect match.",
        )
        v_res_perfect = VerificationResult(
            investigation_id=uuid4(),
            items=[perfect_item],
            overall_contradictions=[],
            overall_uncertainties=[],
            verified_at_timestamp="2026-08-28T15:00:00Z",
        )
        res_perfect = ECIEngine.calculate_eci(v_res_perfect, [
            NormalizedEvidence(
                evidence_id=perfect_item.evidence_id,
                url="https://domain.com/1",
                source_domain="domain.com",
                source_type=SourceType.NEWS_MEDIA,
                discovery_query="q",
                discovery_query_intent="i",
            )
        ])
        assert 0 <= res_perfect.eci_score <= 100

        # Heavily penalized item (contradictions + uncertainties)
        bad_item = EvidenceVerificationItem(
            evidence_id=uuid4(),
            merchant_match=MerchantMatchLevel.UNRELATED,
            temporal_match=TemporalMatchLevel.UNRELATED_TIMING,
            explanation_support=ExplanationSupportLevel.NO_EXPLANATION,
            evidence_strength=EvidenceStrength.CONTRADICTED,
            source_credibility=SourceCredibilityLevel.LOW,
            event_category="none",
            key_facts=[],
            contradictions_identified=["Severe contradiction 1", "Severe contradiction 2"],
            uncertainties_noted=["High ambiguity 1", "High ambiguity 2"],
            reasoning_summary="Contradicted.",
        )
        v_res_bad = VerificationResult(
            investigation_id=uuid4(),
            items=[bad_item],
            overall_contradictions=["Contradiction 1", "Contradiction 2"],
            overall_uncertainties=["Uncertainty 1", "Uncertainty 2"],
            verified_at_timestamp="2026-08-28T15:00:00Z",
        )
        res_bad = ECIEngine.calculate_eci(v_res_bad, [
            NormalizedEvidence(
                evidence_id=bad_item.evidence_id,
                url="https://bad.com/1",
                source_domain="bad.com",
                source_type=SourceType.GENERAL_WEB,
                discovery_query="q",
                discovery_query_intent="i",
            )
        ])
        assert res_bad.eci_score == 0
        assert res_bad.band == ECIBand.LOW

    # --- Invariant 3: Positive Monotonicity ---
    def test_invariant_3_positive_monotonicity(self):
        """Adding genuinely independent supporting evidence must never reduce corroboration."""
        item1 = SCENARIO_1_VERIFICATIONS[0]
        ev1 = SCENARIO_1_EVIDENCE_ITEMS[0]

        res_single = ECIEngine.calculate_eci(
            VerificationResult(
                investigation_id=uuid4(),
                items=[item1],
                overall_contradictions=[],
                overall_uncertainties=[],
                verified_at_timestamp="now",
            ),
            [ev1],
        )

        # Multiple independent sources from Scenario 1
        res_multi = ECIEngine.calculate_eci(
            VerificationResult(
                investigation_id=uuid4(),
                items=SCENARIO_1_VERIFICATIONS,
                overall_contradictions=[],
                overall_uncertainties=[],
                verified_at_timestamp="now",
            ),
            SCENARIO_1_EVIDENCE_ITEMS,
        )

        assert res_multi.eci_score >= res_single.eci_score

    # --- Invariant 4: Contradiction Penalty Monotonicity ---
    def test_invariant_4_contradiction_penalty(self):
        """Introducing a contradiction must reduce or not increase corroboration."""
        clean_v_res = VerificationResult(
            investigation_id=uuid4(),
            items=[SCENARIO_1_VERIFICATIONS[0]],
            overall_contradictions=[],
            overall_uncertainties=[],
            verified_at_timestamp="now",
        )
        clean_res = ECIEngine.calculate_eci(clean_v_res, [SCENARIO_1_EVIDENCE_ITEMS[0]])

        # Same item with contradiction introduced
        contra_v_res = VerificationResult(
            investigation_id=uuid4(),
            items=[SCENARIO_1_VERIFICATIONS[0]],
            overall_contradictions=["Merchant denies launch occurred."],
            overall_uncertainties=[],
            verified_at_timestamp="now",
        )
        contra_res = ECIEngine.calculate_eci(contra_v_res, [SCENARIO_1_EVIDENCE_ITEMS[0]])

        assert contra_res.eci_score < clean_res.eci_score
        assert contra_res.penalty_points > clean_res.penalty_points

    # --- Invariant 5: Deduplication Resistance ---
    def test_invariant_5_deduplication_resistance(self):
        """Re-adding identical evidence from the same domain must not grant extra multi-source bonus."""
        item = SCENARIO_1_VERIFICATIONS[0]
        ev1 = SCENARIO_1_EVIDENCE_ITEMS[0]
        ev1_dup = NormalizedEvidence(
            evidence_id=uuid4(),
            url="https://yourstory.com/mirror",
            source_domain="yourstory.com",  # same domain
            source_type=SourceType.NEWS_MEDIA,
            discovery_query="q",
            discovery_query_intent="i",
        )

        res_single = ECIEngine.calculate_eci(
            VerificationResult(
                investigation_id=uuid4(),
                items=[item],
                overall_contradictions=[],
                overall_uncertainties=[],
                verified_at_timestamp="now",
            ),
            [ev1],
        )

        item_dup = EvidenceVerificationItem(
            evidence_id=ev1_dup.evidence_id,
            merchant_match=item.merchant_match,
            temporal_match=item.temporal_match,
            explanation_support=item.explanation_support,
            evidence_strength=item.evidence_strength,
            source_credibility=item.source_credibility,
            event_category=item.event_category,
            key_facts=item.key_facts,
            contradictions_identified=[],
            uncertainties_noted=[],
            reasoning_summary=item.reasoning_summary,
        )

        res_dup = ECIEngine.calculate_eci(
            VerificationResult(
                investigation_id=uuid4(),
                items=[item, item_dup],
                overall_contradictions=[],
                overall_uncertainties=[],
                verified_at_timestamp="now",
            ),
            [ev1, ev1_dup],
        )

        # Multi-source bonus factor should be 0 because both are from yourstory.com
        corrob_factor = next(f for f in res_dup.factors if f.category == ECIFactorCategory.INDEPENDENT_CORROBORATION)
        assert corrob_factor.points_awarded == 0.0

    # --- Invariant 6: Uncertainty Non-Increase ---
    def test_invariant_6_uncertainty_non_increase(self):
        """Uncertainty must not increase corroboration and can penalize ambiguous evidence."""
        item_clear = SCENARIO_1_VERIFICATIONS[0]
        res_clear = ECIEngine.calculate_eci(
            VerificationResult(
                investigation_id=uuid4(),
                items=[item_clear],
                overall_contradictions=[],
                overall_uncertainties=[],
                verified_at_timestamp="now",
            ),
            [SCENARIO_1_EVIDENCE_ITEMS[0]],
        )

        item_uncertain = EvidenceVerificationItem(
            evidence_id=uuid4(),
            merchant_match=MerchantMatchLevel.UNCERTAIN,
            temporal_match=TemporalMatchLevel.UNCERTAIN,
            explanation_support=ExplanationSupportLevel.UNCERTAIN,
            evidence_strength=EvidenceStrength.WEAK_CIRCUMSTANTIAL,
            source_credibility=SourceCredibilityLevel.UNKNOWN,
            event_category="unknown",
            key_facts=[],
            contradictions_identified=[],
            uncertainties_noted=["Date unclear", "Merchant name ambiguous"],
            reasoning_summary="Unclear.",
        )
        res_uncertain = ECIEngine.calculate_eci(
            VerificationResult(
                investigation_id=uuid4(),
                items=[item_uncertain],
                overall_contradictions=[],
                overall_uncertainties=["Date unclear", "Merchant name ambiguous"],
                verified_at_timestamp="now",
            ),
            [
                NormalizedEvidence(
                    evidence_id=item_uncertain.evidence_id,
                    url="https://domain.com/item",
                    source_domain="domain.com",
                    source_type=SourceType.GENERAL_WEB,
                    discovery_query="q",
                    discovery_query_intent="i",
                )
            ],
        )

        assert res_uncertain.eci_score < res_clear.eci_score
        assert res_uncertain.penalty_points > 0

    # --- Invariant 7: Unrelated Evidence Resistance ---
    def test_invariant_7_unrelated_evidence_resistance(self):
        """Evidence relating to an unrelated merchant or timing must receive 0 match points."""
        unrelated_item = EvidenceVerificationItem(
            evidence_id=uuid4(),
            merchant_match=MerchantMatchLevel.UNRELATED,
            temporal_match=TemporalMatchLevel.UNRELATED_TIMING,
            explanation_support=ExplanationSupportLevel.NO_EXPLANATION,
            evidence_strength=EvidenceStrength.UNSUPPORTED,
            source_credibility=SourceCredibilityLevel.HIGH,
            event_category="other",
            key_facts=["Different company entirely"],
            contradictions_identified=[],
            uncertainties_noted=[],
            reasoning_summary="Unrelated entity.",
        )
        res = ECIEngine.calculate_eci(
            VerificationResult(
                investigation_id=uuid4(),
                items=[unrelated_item],
                overall_contradictions=[],
                overall_uncertainties=[],
                verified_at_timestamp="now",
            ),
            [
                NormalizedEvidence(
                    evidence_id=unrelated_item.evidence_id,
                    url="https://reuters.com/other",
                    source_domain="reuters.com",
                    source_type=SourceType.NEWS_MEDIA,
                    discovery_query="q",
                    discovery_query_intent="i",
                )
            ],
        )

        entity_factor = next(f for f in res.factors if f.category == ECIFactorCategory.ENTITY_MATCH)
        timing_factor = next(f for f in res.factors if f.category == ECIFactorCategory.TEMPORAL_ALIGNMENT)
        assert entity_factor.points_awarded == 0.0
        assert timing_factor.points_awarded == 0.0
        assert res.band == ECIBand.LOW

    # --- Invariant 8: Zero Evidence Explicit State ---
    def test_invariant_8_zero_evidence_explicit_state(self):
        """Zero evidence must produce ECI=0, is_zero_evidence=True, and ECIBand.LOW."""
        v_res = VerificationResult(
            investigation_id=uuid4(),
            items=[],
            overall_contradictions=[],
            overall_uncertainties=[],
            verified_at_timestamp="now",
        )
        res = ECIEngine.calculate_eci(v_res, [])

        assert res.eci_score == 0
        assert res.band == ECIBand.LOW
        assert res.is_zero_evidence is True
        assert res.positive_points == 0.0
        assert res.penalty_points == 0.0
        assert "Zero Evidence" in res.band_label or "Low External Corroboration" in res.band_label

    # --- Invariant 9: Factor Reconciliation ---
    def test_invariant_9_factor_reconciliation(self):
        """Sum of individual factor point awards must reconcile with positive and penalty totals."""
        v_res = VerificationResult(
            investigation_id=uuid4(),
            items=SCENARIO_1_VERIFICATIONS,
            overall_contradictions=[],
            overall_uncertainties=[],
            verified_at_timestamp="now",
        )
        res = ECIEngine.calculate_eci(v_res, SCENARIO_1_EVIDENCE_ITEMS)

        sum_pos = sum(f.points_awarded for f in res.factors if f.points_awarded > 0)
        sum_pen = sum(-f.points_awarded for f in res.factors if f.points_awarded < 0)

        assert round(sum_pos, 2) == round(res.positive_points, 2)
        assert round(sum_pen, 2) == round(res.penalty_points, 2)

    # --- Invariant 10: Qualitative Scenario Outcomes ---
    def test_invariant_10_qualitative_scenario_outcomes(self):
        """
        Relative ordering and qualitative band behavior across synthetic evaluation scenarios:
        Scenario 1 (Strong Viral Launch) > Scenario 3 (Contradicted) > Scenario 2 (Zero Evidence).
        """
        # Scenario 1
        res1 = ECIEngine.calculate_eci(
            VerificationResult(
                investigation_id=uuid4(),
                items=SCENARIO_1_VERIFICATIONS,
                overall_contradictions=[],
                overall_uncertainties=[],
                verified_at_timestamp="now",
            ),
            SCENARIO_1_EVIDENCE_ITEMS,
        )

        # Scenario 2
        res2 = ECIEngine.calculate_eci(
            VerificationResult(
                investigation_id=uuid4(),
                items=SCENARIO_2_VERIFICATIONS,
                overall_contradictions=[],
                overall_uncertainties=[],
                verified_at_timestamp="now",
            ),
            SCENARIO_2_EVIDENCE_ITEMS,
        )

        # Scenario 3
        res3 = ECIEngine.calculate_eci(
            VerificationResult(
                investigation_id=uuid4(),
                items=SCENARIO_3_VERIFICATIONS,
                overall_contradictions=["Merchant official notice explicitly refutes flash sale."],
                overall_uncertainties=[],
                verified_at_timestamp="now",
            ),
            SCENARIO_3_EVIDENCE_ITEMS,
        )

        # Relative ordering
        assert res1.eci_score > res3.eci_score > res2.eci_score

        # Band assertions
        assert res1.band in (ECIBand.STRONG, ECIBand.VERY_STRONG)
        assert res2.eci_score == 0
        assert res2.is_zero_evidence is True
        assert res3.penalty_points > 0  # Contradiction penalty applied

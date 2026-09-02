"""
Deterministic Event Corroboration Index (ECI) Scoring Engine — v1 Heuristic.

Pure Python rule-based scoring engine calculating a transparent, explainable ECI
from verified evidence items.

ARCHITECTURAL PRINCIPLES:
1. DETERMINISTIC: Same verified inputs always produce the exact same score.
2. EXPLAINABLE: Every point added or subtracted is itemized with provenance.
3. BOUNDED: Final score is strictly clamped to [0, 100].
4. INDEPENDENCE-AWARE: Multi-source bonus requires distinct domains.
5. NEUTRAL TERMINOLOGY: ECI measures external corroboration, NOT merchant risk.
"""

from typing import Optional
from uuid import UUID

from app.schemas.eci import (
    ECIBand,
    ECIFactorCategory,
    ECIFactorContribution,
    ECIScoreResult,
)
from app.schemas.evidence import NormalizedEvidence
from app.schemas.verification import (
    EvidenceStrength,
    EvidenceVerificationItem,
    ExplanationSupportLevel,
    MerchantMatchLevel,
    SourceCredibilityLevel,
    TemporalMatchLevel,
    VerificationResult,
)


class ECIEngine:
    """
    Calculates the Event Corroboration Index (ECI) using the v1 heuristic methodology.
    """

    ECI_VERSION = "v1"

    @classmethod
    def calculate_eci(
        cls,
        verification_result: VerificationResult,
        evidence_items: list[NormalizedEvidence],
    ) -> ECIScoreResult:
        """
        Compute the deterministic ECI score and complete factor breakdown.

        Args:
            verification_result: Structured Gemini verification assessments
            evidence_items: Discovered and normalized evidence items

        Returns:
            ECIScoreResult containing the clamped score, qualitative band,
            positive/penalty point totals, and complete factor breakdown.
        """
        # Map evidence items by ID for quick domain/URL lookup
        evidence_by_id = {ev.evidence_id: ev for ev in evidence_items}
        verified_items = verification_result.items

        # --- Handle Zero Evidence Case ---
        if not verified_items:
            zero_factor = ECIFactorContribution(
                factor_id="zero_evidence",
                category=ECIFactorCategory.EXPLANATION_SUPPORT,
                name="No External Evidence Found",
                raw_value="zero_evidence",
                points_awarded=0.0,
                max_possible_points=100.0,
                explanation="No relevant external public web evidence was discovered for this merchant and timeframe.",
                evidence_ids=[],
            )
            return ECIScoreResult(
                eci_score=0,
                band=ECIBand.LOW,
                band_label="Low External Corroboration",
                confidence_level="HIGH",
                eci_version=cls.ECI_VERSION,
                positive_points=0.0,
                penalty_points=0.0,
                factors=[zero_factor],
                is_zero_evidence=True,
            )

        factors: list[ECIFactorContribution] = []
        positive_points = 0.0
        penalty_points = 0.0

        # ============================================================
        # FACTOR 1: Entity Match (Max 25 pts)
        # Evaluates the best confirmed entity match level across evidence
        # ============================================================
        best_entity_item = max(
            verified_items,
            key=lambda x: cls._entity_match_priority(x.merchant_match),
        )
        entity_pts, entity_desc = cls._eval_entity_match(best_entity_item.merchant_match)
        factors.append(
            ECIFactorContribution(
                factor_id="factor_entity_match",
                category=ECIFactorCategory.ENTITY_MATCH,
                name="Merchant Entity Match",
                raw_value=best_entity_item.merchant_match.value,
                points_awarded=entity_pts,
                max_possible_points=25.0,
                explanation=entity_desc,
                evidence_ids=[best_entity_item.evidence_id],
            )
        )
        positive_points += entity_pts

        # ============================================================
        # FACTOR 2: Temporal Alignment (Max 25 pts)
        # Evaluates the closest temporal proximity of the event to anomaly
        # ============================================================
        best_timing_item = max(
            verified_items,
            key=lambda x: cls._temporal_match_priority(x.temporal_match),
        )
        timing_pts, timing_desc = cls._eval_temporal_match(best_timing_item.temporal_match)
        factors.append(
            ECIFactorContribution(
                factor_id="factor_temporal_alignment",
                category=ECIFactorCategory.TEMPORAL_ALIGNMENT,
                name="Temporal Alignment",
                raw_value=best_timing_item.temporal_match.value,
                points_awarded=timing_pts,
                max_possible_points=25.0,
                explanation=timing_desc,
                evidence_ids=[best_timing_item.evidence_id],
            )
        )
        positive_points += timing_pts

        # ============================================================
        # FACTOR 3: Anomaly Explanation Support (Max 20 pts)
        # Evaluates whether the evidence describes a surge-inducing event
        # ============================================================
        best_support_item = max(
            verified_items,
            key=lambda x: cls._support_priority(x.explanation_support),
        )
        support_pts, support_desc = cls._eval_explanation_support(best_support_item.explanation_support)
        factors.append(
            ECIFactorContribution(
                factor_id="factor_explanation_support",
                category=ECIFactorCategory.EXPLANATION_SUPPORT,
                name="Anomaly Explanation Support",
                raw_value=best_support_item.explanation_support.value,
                points_awarded=support_pts,
                max_possible_points=20.0,
                explanation=support_desc,
                evidence_ids=[best_support_item.evidence_id],
            )
        )
        positive_points += support_pts

        # ============================================================
        # FACTOR 4: Source Credibility & Evidence Strength (Max 20 pts)
        # Evaluates the credibility and evidentiary directness of supporting items
        # ============================================================
        best_source_item = max(
            verified_items,
            key=lambda x: cls._source_quality_priority(x.source_credibility, x.evidence_strength),
        )
        source_pts, source_desc = cls._eval_source_quality(
            best_source_item.source_credibility,
            best_source_item.evidence_strength,
        )
        factors.append(
            ECIFactorContribution(
                factor_id="factor_source_credibility",
                category=ECIFactorCategory.SOURCE_CREDIBILITY,
                name="Source Credibility & Directness",
                raw_value=f"{best_source_item.source_credibility.value}+{best_source_item.evidence_strength.value}",
                points_awarded=source_pts,
                max_possible_points=20.0,
                explanation=source_desc,
                evidence_ids=[best_source_item.evidence_id],
            )
        )
        positive_points += source_pts

        # ============================================================
        # FACTOR 5: Independent Corroboration Bonus (Max 10 pts)
        # Rewards corroboration across distinct, independent domain sources
        # ============================================================
        # Count distinct domains among items that provide at least moderate support
        supporting_domains: set[str] = set()
        supporting_ids: list[UUID] = []
        for item in verified_items:
            if item.explanation_support in (
                ExplanationSupportLevel.STRONG_EXPLANATION,
                ExplanationSupportLevel.MODERATE_EXPLANATION,
            ) and item.merchant_match in (
                MerchantMatchLevel.DIRECT_MATCH,
                MerchantMatchLevel.RELATED_ENTITY,
            ):
                ev = evidence_by_id.get(item.evidence_id)
                if ev and ev.source_domain and ev.source_domain != "unknown":
                    supporting_domains.add(ev.source_domain)
                    supporting_ids.append(item.evidence_id)

        corrob_pts = 0.0
        if len(supporting_domains) >= 3:
            corrob_pts = 10.0
            corrob_desc = f"Corroborated across {len(supporting_domains)} independent domains ({', '.join(sorted(supporting_domains)[:3])})."
        elif len(supporting_domains) == 2:
            corrob_pts = 5.0
            corrob_desc = f"Corroborated across 2 independent domains ({', '.join(sorted(supporting_domains))})."
        elif len(supporting_domains) == 1:
            corrob_pts = 0.0
            corrob_desc = "Single source domain identified; no independent cross-source corroboration."
        else:
            corrob_pts = 0.0
            corrob_desc = "No qualifying independent supporting sources identified."

        factors.append(
            ECIFactorContribution(
                factor_id="factor_independent_corroboration",
                category=ECIFactorCategory.INDEPENDENT_CORROBORATION,
                name="Independent Cross-Source Corroboration",
                raw_value=f"{len(supporting_domains)}_independent_domains",
                points_awarded=corrob_pts,
                max_possible_points=10.0,
                explanation=corrob_desc,
                evidence_ids=supporting_ids,
            )
        )
        positive_points += corrob_pts

        # ============================================================
        # FACTOR 6: Contradiction Penalty (-10 to -30 pts)
        # Deducts points for explicit factual refutations or severe conflicts
        # ============================================================
        contradictions_found = verification_result.overall_contradictions
        contra_items = [
            item.evidence_id for item in verified_items
            if item.contradictions_identified or item.evidence_strength == EvidenceStrength.CONTRADICTED
        ]

        contra_penalty = 0.0
        if len(contradictions_found) >= 2 or any(item.evidence_strength == EvidenceStrength.CONTRADICTED for item in verified_items):
            contra_penalty = 25.0
            contra_desc = f"Severe discrepancies identified across sources ({len(contradictions_found)} contradictions recorded)."
        elif len(contradictions_found) == 1:
            contra_penalty = 10.0
            contra_desc = f"One discrepancy identified: {contradictions_found[0]}."
        else:
            contra_penalty = 0.0
            contra_desc = "No factual contradictions identified in discovered evidence."

        if contra_penalty > 0:
            factors.append(
                ECIFactorContribution(
                    factor_id="penalty_contradictions",
                    category=ECIFactorCategory.CONTRADICTION_PENALTY,
                    name="Contradiction Deduction",
                    raw_value=f"{len(contradictions_found)}_contradictions",
                    points_awarded=-contra_penalty,
                    max_possible_points=0.0,
                    explanation=contra_desc,
                    evidence_ids=contra_items,
                )
            )
            penalty_points += contra_penalty

        # ============================================================
        # FACTOR 7: Uncertainty / Evidence Gap Penalty (-5 to -15 pts)
        # Deducts points when major ambiguities remain
        # ============================================================
        uncertainties_found = verification_result.overall_uncertainties
        uncertain_count = sum(
            1 for item in verified_items
            if item.merchant_match == MerchantMatchLevel.UNCERTAIN
            or item.temporal_match == TemporalMatchLevel.UNCERTAIN
            or item.explanation_support == ExplanationSupportLevel.UNCERTAIN
        )

        uncertain_penalty = 0.0
        if uncertain_count >= len(verified_items) and len(verified_items) > 0:
            uncertain_penalty = 12.0
            uncertain_desc = "High ambiguity across all evidence items (unverified dates or entities)."
        elif len(uncertainties_found) >= 2 or uncertain_count >= 2:
            uncertain_penalty = 6.0
            uncertain_desc = f"Moderate unresolved ambiguities noted ({len(uncertainties_found)} gaps identified)."
        else:
            uncertain_penalty = 0.0
            uncertain_desc = "Discovered evidence is clear and unambiguous."

        if uncertain_penalty > 0:
            factors.append(
                ECIFactorContribution(
                    factor_id="penalty_uncertainties",
                    category=ECIFactorCategory.UNCERTAINTY_PENALTY,
                    name="Uncertainty Deduction",
                    raw_value=f"{uncertain_count}_uncertain_attributes",
                    points_awarded=-uncertain_penalty,
                    max_possible_points=0.0,
                    explanation=uncertain_desc,
                    evidence_ids=[],
                )
            )
            penalty_points += uncertain_penalty

        # ============================================================
        # Final Score Calculation and Clamping [0, 100]
        # ============================================================
        raw_score = positive_points - penalty_points
        clamped_score = max(0, min(100, int(round(raw_score))))

        # Band Assignment
        if clamped_score >= 80:
            band = ECIBand.VERY_STRONG
            band_label = "Very Strong External Corroboration"
        elif clamped_score >= 60:
            band = ECIBand.STRONG
            band_label = "Strong External Corroboration"
        elif clamped_score >= 30:
            band = ECIBand.MODERATE
            band_label = "Moderate External Corroboration"
        else:
            band = ECIBand.LOW
            band_label = "Low External Corroboration"

        # Confidence Level Calculation
        if len(verified_items) >= 2 and len(contradictions_found) == 0 and uncertain_penalty == 0:
            confidence = "HIGH"
        elif len(verified_items) >= 1 and len(contradictions_found) <= 1:
            confidence = "MEDIUM"
        else:
            confidence = "LOW"

        return ECIScoreResult(
            eci_score=clamped_score,
            band=band,
            band_label=band_label,
            confidence_level=confidence,
            eci_version=cls.ECI_VERSION,
            positive_points=positive_points,
            penalty_points=penalty_points,
            factors=factors,
            is_zero_evidence=False,
        )

    # --- Priority & Evaluation Helpers ---

    @staticmethod
    def _entity_match_priority(match: MerchantMatchLevel) -> int:
        priorities = {
            MerchantMatchLevel.DIRECT_MATCH: 4,
            MerchantMatchLevel.RELATED_ENTITY: 3,
            MerchantMatchLevel.UNCERTAIN: 2,
            MerchantMatchLevel.UNRELATED: 1,
        }
        return priorities.get(match, 0)

    @staticmethod
    def _eval_entity_match(match: MerchantMatchLevel) -> tuple[float, str]:
        if match == MerchantMatchLevel.DIRECT_MATCH:
            return 25.0, "Direct entity match: evidence explicitly identifies the merchant or domain."
        if match == MerchantMatchLevel.RELATED_ENTITY:
            return 12.0, "Related entity match: evidence references parent company, brand partner, or subsidiary."
        if match == MerchantMatchLevel.UNCERTAIN:
            return 5.0, "Entity match is ambiguous or partially described in text."
        return 0.0, "Evidence refers to an unrelated third party."

    @staticmethod
    def _temporal_match_priority(match: TemporalMatchLevel) -> int:
        priorities = {
            TemporalMatchLevel.EXACT_MATCH: 5,
            TemporalMatchLevel.WINDOW_MATCH: 4,
            TemporalMatchLevel.HISTORICAL_PREVIOUS: 3,
            TemporalMatchLevel.UNCERTAIN: 2,
            TemporalMatchLevel.POST_ANOMALY: 1,
            TemporalMatchLevel.UNRELATED_TIMING: 0,
        }
        return priorities.get(match, 0)

    @staticmethod
    def _eval_temporal_match(match: TemporalMatchLevel) -> tuple[float, str]:
        if match == TemporalMatchLevel.EXACT_MATCH:
            return 25.0, "Exact temporal alignment: event occurred within 0–48 hours of the anomaly."
        if match == TemporalMatchLevel.WINDOW_MATCH:
            return 18.0, "Window alignment: event occurred within the active 7-day anomaly window."
        if match == TemporalMatchLevel.HISTORICAL_PREVIOUS:
            return 5.0, "Historical alignment: event is from a previous period (weeks/months prior)."
        if match == TemporalMatchLevel.UNCERTAIN:
            return 5.0, "Event date could not be precisely verified from the text."
        return 0.0, "Event timing is unrelated to or significantly post-dates the anomaly."

    @staticmethod
    def _support_priority(support: ExplanationSupportLevel) -> int:
        priorities = {
            ExplanationSupportLevel.STRONG_EXPLANATION: 4,
            ExplanationSupportLevel.MODERATE_EXPLANATION: 3,
            ExplanationSupportLevel.WEAK_EXPLANATION: 2,
            ExplanationSupportLevel.UNCERTAIN: 1,
            ExplanationSupportLevel.NO_EXPLANATION: 0,
        }
        return priorities.get(support, 0)

    @staticmethod
    def _eval_explanation_support(support: ExplanationSupportLevel) -> tuple[float, str]:
        if support == ExplanationSupportLevel.STRONG_EXPLANATION:
            return 20.0, "Strong explanation: evidence explicitly describes a major event (e.g. flash sale, viral spike, product launch) explaining transaction surge."
        if support == ExplanationSupportLevel.MODERATE_EXPLANATION:
            return 14.0, "Moderate explanation: evidence provides plausible contributing commercial or promotional context."
        if support == ExplanationSupportLevel.WEAK_EXPLANATION:
            return 6.0, "Weak explanation: minor or tangential promotional mention."
        if support == ExplanationSupportLevel.UNCERTAIN:
            return 4.0, "Explanatory connection to transaction volume surge is uncertain."
        return 0.0, "Evidence does not explain anomalous transaction surge."

    @staticmethod
    def _source_quality_priority(cred: SourceCredibilityLevel, strength: EvidenceStrength) -> int:
        cred_score = {SourceCredibilityLevel.HIGH: 3, SourceCredibilityLevel.MEDIUM: 2, SourceCredibilityLevel.LOW: 1, SourceCredibilityLevel.UNKNOWN: 0}.get(cred, 0)
        str_score = {EvidenceStrength.STRONG_DIRECT: 3, EvidenceStrength.MODERATE_INDIRECT: 2, EvidenceStrength.WEAK_CIRCUMSTANTIAL: 1, EvidenceStrength.UNSUPPORTED: 0, EvidenceStrength.CONTRADICTED: 0}.get(strength, 0)
        return cred_score * 4 + str_score

    @staticmethod
    def _eval_source_quality(cred: SourceCredibilityLevel, strength: EvidenceStrength) -> tuple[float, str]:
        if cred == SourceCredibilityLevel.HIGH and strength == EvidenceStrength.STRONG_DIRECT:
            return 20.0, "High-credibility source providing direct, primary evidence."
        if cred == SourceCredibilityLevel.HIGH and strength == EvidenceStrength.MODERATE_INDIRECT:
            return 16.0, "High-credibility source providing secondary or indirect reporting."
        if cred == SourceCredibilityLevel.MEDIUM and strength in (EvidenceStrength.STRONG_DIRECT, EvidenceStrength.MODERATE_INDIRECT):
            return 13.0, "Established medium-credibility source providing verified evidence."
        if cred == SourceCredibilityLevel.LOW or strength == EvidenceStrength.WEAK_CIRCUMSTANTIAL:
            return 5.0, "Lower-authority source or circumstantial community discussion."
        return 2.0, "Source credibility is unconfirmed or evidentiary strength is weak."

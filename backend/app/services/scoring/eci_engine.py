"""
Deterministic Event Corroboration Index (ECI) Scoring Engine — v1.1 Heuristic.

Pure Python rule-based scoring engine calculating a transparent, explainable ECI
from verified evidence items.

ARCHITECTURAL PRINCIPLES:
1. DETERMINISTIC: Same verified inputs always produce the exact same score.
2. EXPLAINABLE: Every point added or subtracted is itemized with provenance.
3. BOUNDED: Final score is strictly clamped to [0, 100].
4. INDEPENDENCE-AWARE: Multi-source bonus requires distinct claim groups.
5. NEUTRAL TERMINOLOGY: ECI measures external corroboration, NOT merchant risk.

v1.1 CHANGES (Day 4):
6. PER-ITEM ELIGIBILITY: Each evidence item is independently assessed for entity,
   temporal, and source authority eligibility before contributing to the aggregate.
7. ENTITY GATING: UNRELATED items contribute 0 and are excluded with audit reason.
8. TEMPORAL CAUSALITY: POST_ANOMALY/UNRELATED_TIMING items cannot contribute
   causal explanation support.
9. SOURCE AUTHORITY CEILING: LOW credibility / WEAK strength items are capped
   per-item, never globally.
10. CLAIM-GROUP INDEPENDENCE: Uses evidence_group_id when available, falls back
    to domain count. Syndicated copies don't inflate independence.
"""

from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from app.schemas.eci import (
    ECIBand,
    ECIExcludedItem,
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
    VerificationStatus,
)


@dataclass
class _ItemContribution:
    """Internal per-item contribution assessment (not exposed in API)."""
    evidence_id: UUID
    is_eligible: bool
    exclusion_reason: Optional[str]  # None if eligible
    exclusion_explanation: Optional[str]  # Human-readable

    entity_pts: float
    temporal_pts: float
    explanation_pts: float
    source_pts: float
    raw_total: float
    authority_ceiling: float
    capped_total: float

    # Original verification attributes (for factor reporting)
    merchant_match: MerchantMatchLevel
    temporal_match: TemporalMatchLevel
    explanation_support: ExplanationSupportLevel
    source_credibility: SourceCredibilityLevel
    evidence_strength: EvidenceStrength

    # Claim group for independence calculation
    claim_group_id: Optional[str]
    source_domain: str


class ECIEngine:
    """
    Calculates the Event Corroboration Index (ECI) using the v1.1 heuristic methodology.

    v1.1 key change: Per-item eligibility assessment replaces global "best" selection.
    Each evidence item is independently evaluated for entity, temporal, and authority
    eligibility. Ineligible items are excluded from positive contribution but preserved
    in the audit trail. An ineligible item never invalidates other valid evidence.
    """

    ECI_VERSION = "v1.1"

    @classmethod
    def calculate_eci(
        cls,
        verification_result: VerificationResult,
        evidence_items: list[NormalizedEvidence],
        evidence_group_ids: Optional[dict[UUID, str]] = None,
    ) -> ECIScoreResult:
        """
        Compute the deterministic ECI score with per-item eligibility assessment.

        Args:
            verification_result: Structured Gemini verification assessments
            evidence_items: Discovered and normalized evidence items
            evidence_group_ids: Optional mapping of evidence_id → claim group ID
                               (from quality gate annotations). Falls back to
                               domain-based grouping if not provided.

        Returns:
            ECIScoreResult containing the clamped score, qualitative band,
            factor breakdown, and excluded-item audit records.
        """
        # Map evidence items by ID for domain/URL lookup
        evidence_by_id = {ev.evidence_id: ev for ev in evidence_items}
        group_ids = evidence_group_ids or {}

        # Filter to only successfully verified items
        verified_items = [
            item for item in verification_result.items
            if getattr(item, "status", VerificationStatus.VERIFIED) == VerificationStatus.VERIFIED
        ]

        # --- Handle Zero Verified Evidence Case ---
        if not verified_items:
            has_unverified = len(evidence_items) > 0
            zero_factor = ECIFactorContribution(
                factor_id="zero_verified_evidence",
                category=ECIFactorCategory.EXPLANATION_SUPPORT,
                name="No Verified External Evidence" if has_unverified else "No External Evidence Found",
                raw_value="zero_verified_evidence",
                points_awarded=0.0,
                max_possible_points=100.0,
                explanation=(
                    f"External evidence was discovered ({len(evidence_items)} item(s)), but none was successfully verified."
                    if has_unverified
                    else "No relevant external public web evidence was discovered for this merchant and timeframe."
                ),
                evidence_ids=[],
            )
            return ECIScoreResult(
                eci_score=0,
                band=ECIBand.LOW,
                band_label="Low External Corroboration",
                confidence_level="LOW" if has_unverified else "HIGH",
                eci_version=cls.ECI_VERSION,
                positive_points=0.0,
                penalty_points=0.0,
                factors=[zero_factor],
                excluded_items=[],
                eligible_evidence_count=0,
                is_zero_evidence=True,
            )

        # ============================================================
        # PHASE 1: Per-Item Eligibility Assessment (v1.1)
        # ============================================================
        item_contributions: list[_ItemContribution] = []
        excluded_audit: list[ECIExcludedItem] = []

        for item in verified_items:
            ev = evidence_by_id.get(item.evidence_id)
            source_domain = ev.source_domain if ev else "unknown"
            claim_group = group_ids.get(item.evidence_id) if ev else None

            # Compute raw factor points (always, for audit trail)
            entity_pts, _ = cls._eval_entity_match(item.merchant_match)
            temporal_pts, _ = cls._eval_temporal_match(item.temporal_match)
            explanation_pts, _ = cls._eval_explanation_support(item.explanation_support)
            source_pts, _ = cls._eval_source_quality(item.source_credibility, item.evidence_strength)

            # --- Entity Eligibility Gate ---
            if item.merchant_match == MerchantMatchLevel.UNRELATED:
                raw_total = entity_pts + temporal_pts + explanation_pts + source_pts
                item_contributions.append(_ItemContribution(
                    evidence_id=item.evidence_id,
                    is_eligible=False,
                    exclusion_reason="entity_mismatch",
                    exclusion_explanation=(
                        f"Evidence concerns a different entity (merchant_match=UNRELATED). "
                        f"Cannot corroborate this merchant's anomaly."
                    ),
                    entity_pts=0.0, temporal_pts=0.0,
                    explanation_pts=0.0, source_pts=0.0,
                    raw_total=raw_total, authority_ceiling=0.0, capped_total=0.0,
                    merchant_match=item.merchant_match,
                    temporal_match=item.temporal_match,
                    explanation_support=item.explanation_support,
                    source_credibility=item.source_credibility,
                    evidence_strength=item.evidence_strength,
                    claim_group_id=claim_group,
                    source_domain=source_domain,
                ))
                excluded_audit.append(ECIExcludedItem(
                    evidence_id=item.evidence_id,
                    exclusion_reason="entity_mismatch",
                    explanation=(
                        f"Evidence concerns a different entity (merchant_match=UNRELATED). "
                        f"Cannot corroborate this merchant's anomaly."
                    ),
                    raw_contribution=raw_total,
                ))
                continue

            # --- Temporal Causality Gate ---
            # POST_ANOMALY and UNRELATED_TIMING items cannot provide causal explanation
            actual_explanation_pts = explanation_pts
            causal_note = None
            if item.temporal_match in (
                TemporalMatchLevel.POST_ANOMALY,
                TemporalMatchLevel.UNRELATED_TIMING,
            ):
                actual_explanation_pts = 0.0
                causal_note = (
                    f"Temporal match is '{item.temporal_match.value}': "
                    f"event cannot causally explain a preceding anomaly. "
                    f"Explanation support zeroed."
                )

            # --- Source Authority Ceiling ---
            ceiling = cls._authority_ceiling(item.source_credibility, item.evidence_strength)

            raw_total = entity_pts + temporal_pts + actual_explanation_pts + source_pts
            capped_total = min(raw_total, ceiling)

            item_contributions.append(_ItemContribution(
                evidence_id=item.evidence_id,
                is_eligible=True,
                exclusion_reason=None,
                exclusion_explanation=causal_note,
                entity_pts=entity_pts,
                temporal_pts=temporal_pts,
                explanation_pts=actual_explanation_pts,
                source_pts=source_pts,
                raw_total=raw_total,
                authority_ceiling=ceiling,
                capped_total=capped_total,
                merchant_match=item.merchant_match,
                temporal_match=item.temporal_match,
                explanation_support=item.explanation_support,
                source_credibility=item.source_credibility,
                evidence_strength=item.evidence_strength,
                claim_group_id=claim_group,
                source_domain=source_domain,
            ))

        # ============================================================
        # PHASE 2: Aggregate from Eligible Items Only
        # ============================================================
        eligible = [ic for ic in item_contributions if ic.is_eligible]

        # --- Handle Zero Eligible Evidence ---
        if not eligible:
            # Build standard factors with 0.0 awarded for audit completeness
            best_raw_timing = max(item_contributions, key=lambda ic: cls._temporal_match_priority(ic.temporal_match))
            factors = [
                ECIFactorContribution(
                    factor_id="factor_entity_match",
                    category=ECIFactorCategory.ENTITY_MATCH,
                    name="Merchant Entity Match",
                    raw_value="unrelated",
                    points_awarded=0.0,
                    max_possible_points=25.0,
                    explanation="All discovered evidence refers to an unrelated third party.",
                    evidence_ids=[ic.evidence_id for ic in item_contributions],
                ),
                ECIFactorContribution(
                    factor_id="factor_temporal_alignment",
                    category=ECIFactorCategory.TEMPORAL_ALIGNMENT,
                    name="Temporal Alignment",
                    raw_value=best_raw_timing.temporal_match.value,
                    points_awarded=0.0,
                    max_possible_points=25.0,
                    explanation="Event timing is unrelated or evidence is about an unrelated entity.",
                    evidence_ids=[best_raw_timing.evidence_id],
                ),
                ECIFactorContribution(
                    factor_id="factor_explanation_support",
                    category=ECIFactorCategory.EXPLANATION_SUPPORT,
                    name="Anomaly Explanation Support",
                    raw_value="no_explanation",
                    points_awarded=0.0,
                    max_possible_points=20.0,
                    explanation="No eligible evidence provides explanation for the anomaly.",
                    evidence_ids=[],
                ),
                ECIFactorContribution(
                    factor_id="factor_source_credibility",
                    category=ECIFactorCategory.SOURCE_CREDIBILITY,
                    name="Source Credibility & Directness",
                    raw_value="ineligible",
                    points_awarded=0.0,
                    max_possible_points=20.0,
                    explanation="Source credibility discounted because evidence concerns an unrelated entity.",
                    evidence_ids=[],
                ),
                ECIFactorContribution(
                    factor_id="factor_independent_corroboration",
                    category=ECIFactorCategory.INDEPENDENT_CORROBORATION,
                    name="Independent Cross-Source Corroboration",
                    raw_value="0_independent_claim_groups",
                    points_awarded=0.0,
                    max_possible_points=10.0,
                    explanation="No qualifying independent supporting evidence groups identified.",
                    evidence_ids=[],
                ),
            ]

            # Add gating exclusion audit factors
            for ex in excluded_audit:
                factors.append(ECIFactorContribution(
                    factor_id=f"exclusion_{ex.exclusion_reason}",
                    category=ECIFactorCategory.GATING_EXCLUSION,
                    name=f"Evidence Excluded: {ex.exclusion_reason}",
                    raw_value=ex.exclusion_reason,
                    points_awarded=0.0,
                    max_possible_points=0.0,
                    explanation=ex.explanation,
                    evidence_ids=[ex.evidence_id],
                ))

            return ECIScoreResult(
                eci_score=0,
                band=ECIBand.LOW,
                band_label="Low External Corroboration",
                confidence_level="LOW",
                eci_version=cls.ECI_VERSION,
                positive_points=0.0,
                penalty_points=0.0,
                factors=factors,
                excluded_items=excluded_audit,
                eligible_evidence_count=0,
                is_zero_evidence=False,
            )

        factors: list[ECIFactorContribution] = []
        positive_points = 0.0
        penalty_points = 0.0

        # ============================================================
        # FACTOR 1: Entity Match (Max 25 pts) — best ELIGIBLE item
        # ============================================================
        best_entity_ic = max(eligible, key=lambda ic: cls._entity_match_priority(ic.merchant_match))
        entity_pts_awarded, entity_desc = cls._eval_entity_match(best_entity_ic.merchant_match)
        factors.append(ECIFactorContribution(
            factor_id="factor_entity_match",
            category=ECIFactorCategory.ENTITY_MATCH,
            name="Merchant Entity Match",
            raw_value=best_entity_ic.merchant_match.value,
            points_awarded=entity_pts_awarded,
            max_possible_points=25.0,
            explanation=entity_desc,
            evidence_ids=[best_entity_ic.evidence_id],
        ))
        positive_points += entity_pts_awarded

        # ============================================================
        # FACTOR 2: Temporal Alignment (Max 25 pts) — best ELIGIBLE item
        # ============================================================
        best_timing_ic = max(eligible, key=lambda ic: cls._temporal_match_priority(ic.temporal_match))
        timing_pts_awarded, timing_desc = cls._eval_temporal_match(best_timing_ic.temporal_match)
        factors.append(ECIFactorContribution(
            factor_id="factor_temporal_alignment",
            category=ECIFactorCategory.TEMPORAL_ALIGNMENT,
            name="Temporal Alignment",
            raw_value=best_timing_ic.temporal_match.value,
            points_awarded=timing_pts_awarded,
            max_possible_points=25.0,
            explanation=timing_desc,
            evidence_ids=[best_timing_ic.evidence_id],
        ))
        positive_points += timing_pts_awarded

        # ============================================================
        # FACTOR 3: Explanation Support (Max 20 pts) — best CAUSALLY-ELIGIBLE item
        # Causally eligible = eligible AND temporal not POST_ANOMALY/UNRELATED_TIMING
        # ============================================================
        causally_eligible = [
            ic for ic in eligible
            if ic.temporal_match not in (
                TemporalMatchLevel.POST_ANOMALY,
                TemporalMatchLevel.UNRELATED_TIMING,
            )
        ]
        if causally_eligible:
            best_support_ic = max(
                causally_eligible,
                key=lambda ic: cls._support_priority(ic.explanation_support),
            )
            support_pts_awarded, support_desc = cls._eval_explanation_support(best_support_ic.explanation_support)
        else:
            # All eligible items are temporally ineligible for causal explanation
            best_support_ic = eligible[0]
            support_pts_awarded = 0.0
            support_desc = (
                "All eligible evidence items have post-anomaly or unrelated timing. "
                "No item can provide causal explanation for the anomaly."
            )

        factors.append(ECIFactorContribution(
            factor_id="factor_explanation_support",
            category=ECIFactorCategory.EXPLANATION_SUPPORT,
            name="Anomaly Explanation Support",
            raw_value=best_support_ic.explanation_support.value if causally_eligible else "no_causal_evidence",
            points_awarded=support_pts_awarded,
            max_possible_points=20.0,
            explanation=support_desc,
            evidence_ids=[best_support_ic.evidence_id],
        ))
        positive_points += support_pts_awarded

        # ============================================================
        # FACTOR 4: Source Credibility & Evidence Strength (Max 20 pts)
        # ============================================================
        best_source_ic = max(
            eligible,
            key=lambda ic: cls._source_quality_priority(ic.source_credibility, ic.evidence_strength),
        )
        source_pts_awarded, source_desc = cls._eval_source_quality(
            best_source_ic.source_credibility,
            best_source_ic.evidence_strength,
        )
        factors.append(ECIFactorContribution(
            factor_id="factor_source_credibility",
            category=ECIFactorCategory.SOURCE_CREDIBILITY,
            name="Source Credibility & Directness",
            raw_value=f"{best_source_ic.source_credibility.value}+{best_source_ic.evidence_strength.value}",
            points_awarded=source_pts_awarded,
            max_possible_points=20.0,
            explanation=source_desc,
            evidence_ids=[best_source_ic.evidence_id],
        ))
        positive_points += source_pts_awarded

        # ============================================================
        # FACTOR 5: Independent Corroboration Bonus (Max 10 pts)
        # Uses claim-group awareness: distinct claim groups among eligible
        # supporting items, NOT raw domain count.
        # ============================================================
        supporting_groups: dict[str, list[UUID]] = {}
        for ic in eligible:
            if ic.explanation_pts > 0 and ic.merchant_match in (
                MerchantMatchLevel.DIRECT_MATCH,
                MerchantMatchLevel.RELATED_ENTITY,
            ):
                # Use claim_group_id if available, else fall back to domain
                group_key = ic.claim_group_id if ic.claim_group_id else f"domain:{ic.source_domain}"
                if group_key not in supporting_groups:
                    supporting_groups[group_key] = []
                supporting_groups[group_key].append(ic.evidence_id)

        num_independent_groups = len(supporting_groups)
        all_supporting_ids = [eid for ids in supporting_groups.values() for eid in ids]

        if num_independent_groups >= 3:
            corrob_pts = 10.0
            group_labels = sorted(supporting_groups.keys())[:3]
            corrob_desc = f"Corroborated across {num_independent_groups} independent claim groups ({', '.join(group_labels)})."
        elif num_independent_groups == 2:
            corrob_pts = 5.0
            group_labels = sorted(supporting_groups.keys())
            corrob_desc = f"Corroborated across 2 independent claim groups ({', '.join(group_labels)})."
        elif num_independent_groups == 1:
            corrob_pts = 0.0
            corrob_desc = "Single claim group identified; no independent cross-source corroboration."
        else:
            corrob_pts = 0.0
            corrob_desc = "No qualifying independent supporting evidence groups identified."

        factors.append(ECIFactorContribution(
            factor_id="factor_independent_corroboration",
            category=ECIFactorCategory.INDEPENDENT_CORROBORATION,
            name="Independent Cross-Source Corroboration",
            raw_value=f"{num_independent_groups}_independent_claim_groups",
            points_awarded=corrob_pts,
            max_possible_points=10.0,
            explanation=corrob_desc,
            evidence_ids=all_supporting_ids,
        ))
        positive_points += corrob_pts

        # ============================================================
        # APPLY PER-ITEM AUTHORITY CEILING TO AGGREGATE
        # If all eligible items have low authority ceilings, the aggregate
        # positive points cannot exceed the maximum individual ceiling.
        # Scale factors to reconcile perfectly with positive_points.
        # ============================================================
        max_eligible_ceiling = max(ic.authority_ceiling for ic in eligible)
        if positive_points > max_eligible_ceiling and positive_points > 0:
            scale = max_eligible_ceiling / positive_points
            for f in factors:
                if f.points_awarded > 0:
                    f.points_awarded = round(f.points_awarded * scale, 1)
            # Reconcile any float rounding differences
            pos_sum = sum(f.points_awarded for f in factors if f.points_awarded > 0)
            diff = round(max_eligible_ceiling - pos_sum, 1)
            if diff != 0:
                for f in factors:
                    if f.points_awarded > 0:
                        f.points_awarded = round(f.points_awarded + diff, 1)
                        break
            positive_points = max_eligible_ceiling

            factors.append(ECIFactorContribution(
                factor_id="ceiling_authority_cap",
                category=ECIFactorCategory.GATING_EXCLUSION,
                name="Source Authority Ceiling",
                raw_value=f"max_ceiling_{max_eligible_ceiling}",
                points_awarded=0.0,
                max_possible_points=0.0,
                explanation=(
                    f"Aggregate positive points were capped to {max_eligible_ceiling:.0f} "
                    f"because all eligible sources have limited authority (e.g. unverified social posts)."
                ),
                evidence_ids=[ic.evidence_id for ic in eligible],
            ))

        # ============================================================
        # FACTOR 6: Contradiction Penalty (-10 to -25 pts) — unchanged
        # ============================================================
        contradictions_found = verification_result.overall_contradictions
        contra_items = [
            item.evidence_id for item in verified_items
            if item.contradictions_identified or item.evidence_strength == EvidenceStrength.CONTRADICTED
        ]

        contra_penalty = 0.0
        if len(contradictions_found) >= 2 or any(
            item.evidence_strength == EvidenceStrength.CONTRADICTED for item in verified_items
        ):
            contra_penalty = 25.0
            contra_desc = f"Severe discrepancies identified across sources ({len(contradictions_found)} contradictions recorded)."
        elif len(contradictions_found) == 1:
            contra_penalty = 10.0
            contra_desc = f"One discrepancy identified: {contradictions_found[0]}."
        else:
            contra_penalty = 0.0
            contra_desc = "No factual contradictions identified in discovered evidence."

        if contra_penalty > 0:
            factors.append(ECIFactorContribution(
                factor_id="penalty_contradictions",
                category=ECIFactorCategory.CONTRADICTION_PENALTY,
                name="Contradiction Deduction",
                raw_value=f"{len(contradictions_found)}_contradictions",
                points_awarded=-contra_penalty,
                max_possible_points=0.0,
                explanation=contra_desc,
                evidence_ids=contra_items,
            ))
            penalty_points += contra_penalty

        # ============================================================
        # FACTOR 7: Uncertainty Penalty (-6 to -12 pts) — unchanged
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
            factors.append(ECIFactorContribution(
                factor_id="penalty_uncertainties",
                category=ECIFactorCategory.UNCERTAINTY_PENALTY,
                name="Uncertainty Deduction",
                raw_value=f"{uncertain_count}_uncertain_attributes",
                points_awarded=-uncertain_penalty,
                max_possible_points=0.0,
                explanation=uncertain_desc,
                evidence_ids=[],
            ))
            penalty_points += uncertain_penalty

        # ============================================================
        # Add gating exclusion audit factors for excluded items
        # ============================================================
        if excluded_audit:
            for ex in excluded_audit:
                factors.append(ECIFactorContribution(
                    factor_id=f"exclusion_{ex.exclusion_reason}",
                    category=ECIFactorCategory.GATING_EXCLUSION,
                    name=f"Evidence Excluded: {ex.exclusion_reason}",
                    raw_value=ex.exclusion_reason,
                    points_awarded=0.0,
                    max_possible_points=0.0,
                    explanation=ex.explanation,
                    evidence_ids=[ex.evidence_id],
                ))

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
        if len(eligible) >= 2 and len(contradictions_found) == 0 and uncertain_penalty == 0:
            confidence = "HIGH"
        elif len(eligible) >= 1 and len(contradictions_found) <= 1:
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
            excluded_items=excluded_audit,
            eligible_evidence_count=len(eligible),
            is_zero_evidence=False,
        )

    # --- Authority Ceiling (v1.1) ---

    @staticmethod
    def _authority_ceiling(cred: SourceCredibilityLevel, strength: EvidenceStrength) -> float:
        """
        Per-item authority ceiling based on source credibility and evidence strength.

        Prevents low-authority sources from independently producing strong corroboration
        scores, regardless of entity and temporal alignment.

        This is NOT a global cap — it is applied per evidence item. A high-authority
        item in the same investigation is unaffected by a low-authority item's ceiling.
        """
        if strength == EvidenceStrength.CONTRADICTED:
            return 0.0
        if strength == EvidenceStrength.UNSUPPORTED:
            return 15.0
        if cred == SourceCredibilityLevel.LOW or strength == EvidenceStrength.WEAK_CIRCUMSTANTIAL:
            return 29.0
        if cred == SourceCredibilityLevel.UNKNOWN:
            return 29.0
        if cred in (SourceCredibilityLevel.HIGH, SourceCredibilityLevel.MEDIUM):
            return 100.0
        return 29.0

    # --- Priority & Evaluation Helpers (unchanged from v1) ---

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

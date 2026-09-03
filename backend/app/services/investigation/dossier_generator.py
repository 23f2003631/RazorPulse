"""
Evidence Dossier Generator Service.

Synthesizes the complete Evidence Dossier for the human risk analyst,
combining the anomaly context, verified citations, deterministic ECI breakdown,
unresolved gaps, and recommended review checklist.
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from app.schemas.dossier import (
    AnomalySummary,
    EvidenceCitation,
    EvidenceDossier,
)
from app.schemas.eci import ECIScoreResult
from app.schemas.evidence import NormalizedEvidence
from app.schemas.pipeline_metadata import PipelineMetadata
from app.schemas.verification import (
    MerchantMatchLevel,
    TemporalMatchLevel,
    VerificationResult,
    VerificationStatus,
)
from app.services.evidence_quality import EvidenceQualitySummary


class DossierGenerator:
    """
    Constructs an EvidenceDossier from investigation results.
    """

    @classmethod
    def generate_dossier(
        cls,
        investigation_id: UUID,
        risk_event: dict,
        evidence_items: list[NormalizedEvidence],
        verification_result: VerificationResult,
        eci_result: ECIScoreResult,
        executed_queries: list[dict],
        pipeline_metadata: Optional[PipelineMetadata] = None,
        quality_summary: Optional[EvidenceQualitySummary] = None,
    ) -> EvidenceDossier:
        """
        Assemble the complete analyst-facing Evidence Dossier.

        Args:
            investigation_id: Investigation UUID
            risk_event: Dict containing risk event details and merchant info
            evidence_items: Normalized evidence list
            verification_result: Gemini verification results
            eci_result: Deterministic ECI score result
            executed_queries: Search queries executed by Exa

        Returns:
            EvidenceDossier ready for analyst review
        """
        merchant_info = risk_event.get("merchants", {}) or {}
        merchant_name = risk_event.get("merchant_name") or merchant_info.get("merchant_name", "Unknown Merchant")
        merchant_domain = risk_event.get("merchant_domain") or merchant_info.get("merchant_domain")

        occurred_at_raw = risk_event.get("occurred_at")
        if isinstance(occurred_at_raw, str):
            occurred_at_dt = datetime.fromisoformat(occurred_at_raw)
        elif isinstance(occurred_at_raw, datetime):
            occurred_at_dt = occurred_at_raw
        else:
            occurred_at_dt = datetime.now(timezone.utc)

        risk_reason = risk_event.get("risk_reason")

        # 1. Anomaly Summary Snapshot
        anomaly_summary = AnomalySummary(
            risk_event_id=UUID(str(risk_event["id"])),
            merchant_name=merchant_name,
            merchant_domain=merchant_domain,
            anomaly_type=str(risk_event.get("anomaly_type", "unusual_pattern")),
            occurred_at=occurred_at_dt,
            baseline_transaction_count=risk_event.get("baseline_transaction_count"),
            observed_transaction_count=risk_event.get("observed_transaction_count"),
            percentage_change=risk_event.get("percentage_change"),
            transaction_amount=risk_event.get("transaction_amount"),
            currency=str(risk_event.get("currency", "INR")),
            risk_reason=risk_reason,
            geographic_info=risk_event.get("geographic_info"),
        )

        # 2. Categorize items by status
        verified_items = [
            item for item in verification_result.items
            if getattr(item, "status", VerificationStatus.VERIFIED) == VerificationStatus.VERIFIED
        ]
        failed_items = [
            item for item in verification_result.items
            if getattr(item, "status", None) == VerificationStatus.FAILED
        ]
        skipped_items = [
            item for item in verification_result.items
            if getattr(item, "status", None) == VerificationStatus.SKIPPED
        ]

        # 3. Build Evidence Citations (Only for VERIFIED items)
        citations: list[EvidenceCitation] = []
        evidence_by_id = {ev.evidence_id: ev for ev in evidence_items}

        for idx, item in enumerate(verified_items, start=1):
            ev = evidence_by_id.get(item.evidence_id)
            if ev:
                first_fact = item.key_facts[0] if item.key_facts else item.reasoning_summary
                citations.append(
                    EvidenceCitation(
                        citation_id=f"[E{idx}]",
                        evidence_id=item.evidence_id,
                        url=ev.url,
                        title=ev.title,
                        source_domain=ev.source_domain,
                        source_type=ev.source_type.value,
                        key_fact=first_fact,
                        temporal_match=item.temporal_match.value,
                        source_credibility=item.source_credibility.value,
                    )
                )

        # 4. Executive Summary
        executive_summary = cls._generate_executive_summary(
            merchant_name=merchant_name,
            anomaly_summary=anomaly_summary,
            eci_result=eci_result,
            evidence_count=len(evidence_items),
            verified_count=len(verified_items),
            failed_count=len(failed_items),
            contradictions=verification_result.overall_contradictions,
        )

        # 5. Gaps and Uncertainties
        evidence_gaps: list[str] = []
        if len(evidence_items) == 0:
            evidence_gaps.append("No public external coverage, press release, or merchant announcement found for this anomaly period.")
        elif len(verified_items) == 0 and len(evidence_items) > 0:
            evidence_gaps.append(
                f"External evidence was discovered ({len(evidence_items)} item(s)), but Gemini verification was incomplete due to provider limitations."
            )
        else:
            if failed_items:
                evidence_gaps.append(f"{len(failed_items)} discovered item(s) could not be verified by Gemini due to provider limits.")
            if skipped_items:
                evidence_gaps.append(f"{len(skipped_items)} lower-priority item(s) were skipped from LLM verification to optimize processing efficiency.")
            if len(verified_items) == 1:
                evidence_gaps.append("Only a single source was verified; lacks independent multi-domain corroboration.")

        # 6. Analyst Review Checklist (Evidence-ID referencing)
        checklist = cls._build_review_checklist(
            anomaly_summary=anomaly_summary,
            eci_result=eci_result,
            citations=citations,
            verification_result=verification_result,
            quality_summary=quality_summary,
        )

        # Append quality exclusions/advisories to evidence_gaps if present
        if quality_summary:
            for excl in quality_summary.exclusion_reasons[:3]:
                evidence_gaps.append(f"Quality gate exclusion: {excl}")
            for flag in quality_summary.flagged_reasons[:2]:
                evidence_gaps.append(f"Quality advisory: {flag}")

        return EvidenceDossier(
            investigation_id=investigation_id,
            generated_at=datetime.now(timezone.utc),
            pipeline_version="0.3.0",
            eci_version=eci_result.eci_version,
            pipeline_metadata=pipeline_metadata,
            anomaly_context=anomaly_summary,
            executive_summary=executive_summary,
            eci_result=eci_result,
            evidence_count=len(evidence_items),
            evidence_citations=citations,
            contradictions=verification_result.overall_contradictions,
            evidence_gaps=evidence_gaps,
            verification_uncertainties=verification_result.overall_uncertainties,
            analyst_review_checklist=checklist,
            search_queries_used=executed_queries,
        )

    @classmethod
    def _generate_executive_summary(
        cls,
        merchant_name: str,
        anomaly_summary: AnomalySummary,
        eci_result: ECIScoreResult,
        evidence_count: int,
        verified_count: int,
        failed_count: int,
        contradictions: list[str],
    ) -> str:
        pct_text = f"+{anomaly_summary.percentage_change}%" if anomaly_summary.percentage_change else "anomalous"
        if eci_result.is_zero_evidence:
            if failed_count > 0:
                return (
                    f"RazorPulse discovered {evidence_count} external evidence item(s) for {merchant_name}, "
                    f"but Gemini verification could not be completed due to provider quota/availability constraints. "
                    f"External Corroboration is Low (ECI: 0/100). "
                    f"The analyst should proceed with standard internal verification."
                )
            return (
                f"RazorPulse investigated an observed {pct_text} surge in transaction activity for {merchant_name} "
                f"on {anomaly_summary.occurred_at.strftime('%Y-%m-%d')}. "
                f"No relevant public external web evidence, media coverage, or announcements were discovered. "
                f"External Corroboration is Low (ECI: 0/100). "
                f"The analyst should proceed with standard internal verification."
            )

        if eci_result.eci_score >= 60:
            summary = (
                f"RazorPulse discovered {evidence_count} external evidence item(s) for {merchant_name} ({verified_count} verified). "
                f"Verified evidence indicates a public real-world event matching the timing of the {pct_text} transaction anomaly. "
                f"Event Corroboration Index is {eci_result.eci_score}/100 ({eci_result.band_label})."
            )
            if contradictions:
                summary += f" Note: {len(contradictions)} potential discrepancy was flagged for manual review."
            return summary

        if eci_result.eci_score >= 30:
            return (
                f"RazorPulse discovered {evidence_count} external evidence item(s) relating to {merchant_name} ({verified_count} verified). "
                f"Verified items provide moderate contextual context but exhibit minor temporal or entity ambiguity. "
                f"Event Corroboration Index is {eci_result.eci_score}/100 ({eci_result.band_label})."
            )

        return (
            f"RazorPulse discovered {evidence_count} external evidence item(s) for {merchant_name} ({verified_count} verified), "
            f"but verification indicates weak, unaligned, or contradicted contextual connection to the transaction anomaly. "
            f"Event Corroboration Index is {eci_result.eci_score}/100 ({eci_result.band_label})."
        )

    @classmethod
    def _build_review_checklist(
        cls,
        anomaly_summary: AnomalySummary,
        eci_result: ECIScoreResult,
        citations: list[EvidenceCitation],
        verification_result: VerificationResult,
        quality_summary: Optional[EvidenceQualitySummary] = None,
    ) -> list[str]:
        items: list[str] = [
            f"Review transaction settlement accounts and merchant profile for {anomaly_summary.merchant_name}.",
            "Check current dispute / chargeback trajectory relative to increased transaction velocity.",
        ]

        if eci_result.is_zero_evidence:
            items.insert(0, "Contact merchant directly or review internal support communications regarding recent promotional activity.")
        elif eci_result.eci_score >= 60:
            items.insert(0, "Verify that the reported external event/campaign corresponds to the merchant's registered category and typical basket size.")

        # Map evidence_id to citation_id for clear provenance in checklist
        citation_by_ev_id = {c.evidence_id: c for c in citations}

        # Item-specific provenance checks referencing citation IDs
        for item in verification_result.items:
            citation = citation_by_ev_id.get(item.evidence_id)
            ref = f"{citation.citation_id} ({citation.source_domain})" if citation else "discovered evidence"

            if item.contradictions_identified:
                items.append(f"Investigate contradiction / discrepancy flagged in {ref}: {item.contradictions_identified[0]}")
            if item.temporal_match in (TemporalMatchLevel.UNCERTAIN, TemporalMatchLevel.HISTORICAL_PREVIOUS):
                items.append(f"Verify publication timeframe for {ref} -- temporal match assessed as '{item.temporal_match.value}'.")
            if item.merchant_match in (MerchantMatchLevel.RELATED_ENTITY, MerchantMatchLevel.UNCERTAIN):
                items.append(f"Confirm legal or commercial relationship for {ref} -- entity match assessed as '{item.merchant_match.value}'.")

        # Fallback if contradiction recorded in overall but not caught per-item
        if verification_result.overall_contradictions and not any("Investigate contradiction flagged in" in it for it in items):
            items.append(f"Investigate identified evidence discrepancy: {verification_result.overall_contradictions[0]}")

        # Single source dependency notice
        if len(citations) == 1:
            items.append(f"Corroboration relies solely on single source {citations[0].citation_id} ({citations[0].source_domain}); verify through secondary channels.")

        # Claim syndication note
        if quality_summary and quality_summary.unique_claim_groups < len(citations) and len(citations) >= 2:
            items.append(
                f"Note: Multiple sources appear to syndicate a single announcement "
                f"({quality_summary.unique_claim_groups} unique claim cluster(s) among {len(citations)} sources). Check for independent news reporting."
            )

        return items

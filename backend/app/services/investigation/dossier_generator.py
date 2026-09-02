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
from app.schemas.verification import VerificationResult


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
            risk_reason=risk_event.get("risk_reason"),
            geographic_info=risk_event.get("geographic_info"),
        )

        # 2. Build Evidence Citations
        citations: list[EvidenceCitation] = []
        evidence_by_id = {ev.evidence_id: ev for ev in evidence_items}

        for idx, item in enumerate(verification_result.items, start=1):
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

        # 3. Executive Summary
        executive_summary = cls._generate_executive_summary(
            merchant_name=merchant_name,
            anomaly_summary=anomaly_summary,
            eci_result=eci_result,
            evidence_count=len(evidence_items),
            contradictions=verification_result.overall_contradictions,
        )

        # 4. Gaps and Uncertainties
        evidence_gaps: list[str] = []
        if len(evidence_items) == 0:
            evidence_gaps.append("No public external coverage, press release, or merchant announcement found for this anomaly period.")
        elif len(evidence_items) == 1:
            evidence_gaps.append("Only a single source discovered; lacks independent multi-domain corroboration.")

        # 5. Analyst Review Checklist
        checklist = cls._build_review_checklist(
            anomaly_summary=anomaly_summary,
            eci_result=eci_result,
            contradictions=verification_result.overall_contradictions,
        )

        return EvidenceDossier(
            investigation_id=investigation_id,
            generated_at=datetime.now(timezone.utc),
            pipeline_version="0.2.0",
            eci_version=eci_result.eci_version,
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
        contradictions: list[str],
    ) -> str:
        pct_text = f"+{anomaly_summary.percentage_change}%" if anomaly_summary.percentage_change else "anomalous"
        if eci_result.is_zero_evidence:
            return (
                f"RazorPulse investigated an observed {pct_text} surge in transaction activity for {merchant_name} "
                f"on {anomaly_summary.occurred_at.strftime('%Y-%m-%d')}. "
                f"No relevant public external web evidence, media coverage, or announcements were discovered. "
                f"External Corroboration is Low (ECI: 0/100). "
                f"The analyst should proceed with standard internal verification."
            )

        if eci_result.eci_score >= 60:
            summary = (
                f"RazorPulse discovered {evidence_count} external evidence item(s) for {merchant_name}. "
                f"Verified evidence indicates a public real-world event matching the timing of the {pct_text} transaction anomaly. "
                f"Event Corroboration Index is {eci_result.eci_score}/100 ({eci_result.band_label})."
            )
            if contradictions:
                summary += f" Note: {len(contradictions)} potential discrepancy was flagged for manual review."
            return summary

        if eci_result.eci_score >= 30:
            return (
                f"RazorPulse discovered {evidence_count} external evidence item(s) relating to {merchant_name}. "
                f"Discovered items provide moderate contextual context but exhibit minor temporal or entity ambiguity. "
                f"Event Corroboration Index is {eci_result.eci_score}/100 ({eci_result.band_label})."
            )

        return (
            f"RazorPulse discovered {evidence_count} external evidence item(s) for {merchant_name}, "
            f"but verification indicates weak, unaligned, or contradicted contextual connection to the transaction anomaly. "
            f"Event Corroboration Index is {eci_result.eci_score}/100 ({eci_result.band_label})."
        )

    @classmethod
    def _build_review_checklist(
        cls,
        anomaly_summary: AnomalySummary,
        eci_result: ECIScoreResult,
        contradictions: list[str],
    ) -> list[str]:
        items: list[str] = [
            f"Review transaction settlement accounts and merchant profile for {anomaly_summary.merchant_name}.",
            "Check current dispute / chargeback trajectory relative to increased transaction velocity.",
        ]

        if eci_result.is_zero_evidence:
            items.insert(0, "Contact merchant directly or review internal support communications regarding recent promotional activity.")
        elif eci_result.eci_score >= 60:
            items.insert(0, "Verify that the reported external event/campaign corresponds to the merchant's registered category and typical basket size.")

        if contradictions:
            items.append(f"Investigate identified evidence discrepancy: {contradictions[0]}")

        return items

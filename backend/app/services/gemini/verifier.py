"""
Gemini Evidence Verifier Service.

Executes structured verification of discovered evidence items using Google Gemini
with strict Pydantic response schema enforcement.
"""

from datetime import datetime, timezone
import json
from typing import Optional
from uuid import UUID

from google.genai import types

from app.core.exceptions import GeminiServiceError
from app.core.logging import get_logger
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
from app.services.gemini.client import GeminiClient
from app.services.gemini.prompts import (
    VERIFICATION_SYSTEM_INSTRUCTION,
    build_evidence_verification_prompt,
)
from app.services.gemini.retry import with_gemini_retry

logger = get_logger("gemini_verifier")


class GeminiVerifier:
    """
    Evaluates discovered evidence items against a risk anomaly using Gemini.
    """

    def __init__(self, client: Optional[GeminiClient] = None):
        """Initialize with an optional injected client."""
        self._client = client

    def _get_client(self) -> GeminiClient:
        if self._client is None:
            self._client = GeminiClient()
        return self._client

    def verify_single_evidence(
        self,
        evidence: NormalizedEvidence,
        merchant_name: str,
        merchant_domain: Optional[str] = None,
        occurred_at: Optional[datetime] = None,
        anomaly_type: str = "transaction_velocity_spike",
        risk_reason: Optional[str] = None,
    ) -> EvidenceVerificationItem:
        """
        Verify a single evidence item using structured Gemini output.

        Args:
            evidence: The NormalizedEvidence item to assess
            merchant_name: Name of the merchant
            merchant_domain: Domain of merchant
            occurred_at: Anomaly timestamp
            anomaly_type: Anomaly category
            risk_reason: Risk engine reason string

        Returns:
            EvidenceVerificationItem with structured verification assessment
        """
        client = self._get_client()
        occurred_at_str = occurred_at.isoformat() if occurred_at else "Unknown date"

        prompt = build_evidence_verification_prompt(
            merchant_name=merchant_name,
            merchant_domain=merchant_domain,
            anomaly_type=anomaly_type,
            occurred_at_str=occurred_at_str,
            risk_reason=risk_reason,
            evidence_id=str(evidence.evidence_id),
            evidence_url=evidence.url,
            evidence_title=evidence.title,
            source_domain=evidence.source_domain,
            source_type=evidence.source_type.value,
            published_at=evidence.published_at,
            content_snippet=evidence.content_snippet,
            highlights=evidence.highlights,
        )

        try:
            logger.info("Calling Gemini for evidence ID: {}", evidence.evidence_id)
            config = types.GenerateContentConfig(
                system_instruction=VERIFICATION_SYSTEM_INSTRUCTION,
                response_mime_type="application/json",
                response_schema=EvidenceVerificationItem,
                temperature=0.1,  # Low temperature for deterministic analysis
            )
            response = with_gemini_retry(
                lambda: client._client.models.generate_content(
                    model=client._model_name,
                    contents=prompt,
                    config=config,
                ),
                operation_name=f"verify_evidence_{evidence.evidence_id}",
            )

            raw_text = response.text.strip() if response.text else ""
            parsed = json.loads(raw_text)

            # Ensure evidence_id in response matches requested ID
            parsed["evidence_id"] = evidence.evidence_id
            verified_item = EvidenceVerificationItem.model_validate(parsed)
            logger.info(
                "Evidence {} verified: entity={}, timing={}, support={}",
                evidence.evidence_id,
                verified_item.merchant_match.value,
                verified_item.temporal_match.value,
                verified_item.explanation_support.value,
            )
            return verified_item

        except Exception as e:
            logger.error("Gemini verification failed for evidence {}: {}", evidence.evidence_id, str(e))
            # Safe, neutral fallback item preserving error state without fabricating facts
            return EvidenceVerificationItem(
                evidence_id=evidence.evidence_id,
                merchant_match=MerchantMatchLevel.UNCERTAIN,
                temporal_match=TemporalMatchLevel.UNCERTAIN,
                explanation_support=ExplanationSupportLevel.UNCERTAIN,
                evidence_strength=EvidenceStrength.WEAK_CIRCUMSTANTIAL,
                source_credibility=SourceCredibilityLevel.UNKNOWN,
                event_category="unverified",
                key_facts=[],
                contradictions_identified=[],
                uncertainties_noted=[f"Automated verification error: {str(e)}"],
                reasoning_summary="Verification could not be completed due to model evaluation failure.",
            )

    def verify_all_evidence(
        self,
        investigation_id: UUID,
        evidence_items: list[NormalizedEvidence],
        merchant_name: str,
        merchant_domain: Optional[str] = None,
        occurred_at: Optional[datetime] = None,
        anomaly_type: str = "transaction_velocity_spike",
        risk_reason: Optional[str] = None,
    ) -> VerificationResult:
        """
        Verify all discovered evidence items for an investigation.

        Args:
            investigation_id: UUID of investigation
            evidence_items: List of normalized evidence items
            merchant_name: Merchant name
            merchant_domain: Merchant domain
            occurred_at: Anomaly timestamp
            anomaly_type: Anomaly category
            risk_reason: Risk engine reason

        Returns:
            VerificationResult containing all item assessments and consolidated findings
        """
        verified_items: list[EvidenceVerificationItem] = []
        all_contradictions: set[str] = set()
        all_uncertainties: set[str] = set()

        for ev in evidence_items:
            item_result = self.verify_single_evidence(
                evidence=ev,
                merchant_name=merchant_name,
                merchant_domain=merchant_domain,
                occurred_at=occurred_at,
                anomaly_type=anomaly_type,
                risk_reason=risk_reason,
            )
            verified_items.append(item_result)
            for c in item_result.contradictions_identified:
                if c.strip():
                    all_contradictions.add(c.strip())
            for u in item_result.uncertainties_noted:
                if u.strip():
                    all_uncertainties.add(u.strip())

        return VerificationResult(
            investigation_id=investigation_id,
            items=verified_items,
            overall_contradictions=list(all_contradictions),
            overall_uncertainties=list(all_uncertainties),
            verified_at_timestamp=datetime.now(timezone.utc).isoformat(),
        )

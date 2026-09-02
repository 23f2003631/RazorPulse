"""
Gemini Evidence Verifier Service.

Executes structured batch verification of top discovered evidence items using Google Gemini
with strict Pydantic response schema enforcement.
"""

from datetime import datetime, timezone
import json
from typing import Optional
from uuid import UUID

from google.genai import types

from app.config.settings import get_settings
from app.core.exceptions import GeminiServiceError
from app.core.logging import get_logger
from app.schemas.evidence import NormalizedEvidence, SourceType
from app.schemas.verification import (
    BatchEvidenceVerificationResponse,
    EvidenceStrength,
    EvidenceVerificationItem,
    ExplanationSupportLevel,
    MerchantMatchLevel,
    SourceCredibilityLevel,
    TemporalMatchLevel,
    VerificationResult,
    VerificationStatus,
)
from app.services.gemini.client import GeminiClient
from app.services.gemini.prompts import (
    VERIFICATION_SYSTEM_INSTRUCTION,
    build_batch_evidence_verification_prompt,
    build_evidence_verification_prompt,
)
from app.services.gemini.retry import with_gemini_retry

logger = get_logger("gemini_verifier")


def rank_evidence_item(item: NormalizedEvidence) -> tuple:
    """
    Deterministic ranking key for evidence selection (higher tuple is better).

    Priority:
    1. Source type quality (Official Merchant > News / PR > Industry > Social > Web)
    2. Highlights count (more highlights indicate richer key facts)
    3. External relevance score (from Exa)
    4. Publication timestamp availability
    5. Content snippet length
    """
    source_priority = {
        SourceType.MERCHANT_OFFICIAL: 5,
        SourceType.NEWS_MEDIA: 4,
        SourceType.PRESS_RELEASE: 4,
        SourceType.INDUSTRY_PORTAL: 3,
        SourceType.SOCIAL_COMMUNITY: 2,
        SourceType.GENERAL_WEB: 1,
    }.get(item.source_type, 0)

    highlights_count = len(item.highlights) if item.highlights else 0
    ext_score = item.external_score if item.external_score is not None else 0.0
    has_date = 1 if item.published_at else 0
    snippet_len = len(item.content_snippet) if item.content_snippet else 0

    return (source_priority, highlights_count, ext_score, has_date, snippet_len)


def select_top_evidence(
    evidence_items: list[NormalizedEvidence],
    max_items: int = 4,
) -> tuple[list[NormalizedEvidence], list[NormalizedEvidence]]:
    """
    Deterministically partition evidence items into top-ranked selected items
    and remaining skipped items.

    Args:
        evidence_items: List of normalized evidence items
        max_items: Maximum items to select for Gemini verification

    Returns:
        tuple of (selected_items, skipped_items)
    """
    if not evidence_items:
        return [], []

    # Sort descending by deterministic ranking key
    sorted_items = sorted(evidence_items, key=rank_evidence_item, reverse=True)
    selected = sorted_items[:max_items]
    skipped = sorted_items[max_items:]
    return selected, skipped


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
            logger.info("Calling Gemini for single evidence ID: {}", evidence.evidence_id)
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

            # Ensure evidence_id and status match
            parsed["evidence_id"] = evidence.evidence_id
            parsed["status"] = VerificationStatus.VERIFIED
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
            # Safe, neutral failure item preserving error state without fabricating positive facts
            return EvidenceVerificationItem(
                evidence_id=evidence.evidence_id,
                status=VerificationStatus.FAILED,
                failure_reason=str(e),
                merchant_match=MerchantMatchLevel.UNCERTAIN,
                temporal_match=TemporalMatchLevel.UNCERTAIN,
                explanation_support=ExplanationSupportLevel.UNCERTAIN,
                evidence_strength=EvidenceStrength.WEAK_CIRCUMSTANTIAL,
                source_credibility=SourceCredibilityLevel.UNKNOWN,
                event_category=None,
                key_facts=[],
                contradictions_identified=[],
                uncertainties_noted=[f"Automated verification error: {str(e)}"],
                reasoning_summary=f"Verification failed: {str(e)}",
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
        max_evidence_items: Optional[int] = None,
    ) -> VerificationResult:
        """
        Verify discovered evidence items for an investigation in a single batch Gemini call.

        Selects top N evidence items (default 4) for Gemini verification.
        Unselected items are marked as SKIPPED.

        Args:
            investigation_id: UUID of investigation
            evidence_items: List of normalized evidence items
            merchant_name: Merchant name
            merchant_domain: Merchant domain
            occurred_at: Anomaly timestamp
            anomaly_type: Anomaly category
            risk_reason: Risk engine reason
            max_evidence_items: Optional override for max evidence items to verify

        Returns:
            VerificationResult containing all item assessments (VERIFIED, FAILED, SKIPPED)
        """
        if not evidence_items:
            return VerificationResult(
                investigation_id=investigation_id,
                items=[],
                overall_contradictions=[],
                overall_uncertainties=["No external web evidence found to verify."],
                verified_at_timestamp=datetime.now(timezone.utc).isoformat(),
            )

        settings = get_settings()
        limit = max_evidence_items or settings.GEMINI_MAX_EVIDENCE_ITEMS
        selected_items, skipped_items = select_top_evidence(evidence_items, max_items=limit)

        logger.info(
            "Evidence selection: {} total items -> {} selected for Gemini batch verification, {} skipped",
            len(evidence_items),
            len(selected_items),
            len(skipped_items),
        )

        all_verification_items: list[EvidenceVerificationItem] = []
        all_contradictions: set[str] = set()
        all_uncertainties: set[str] = set()

        client = self._get_client()
        occurred_at_str = occurred_at.isoformat() if occurred_at else "Unknown date"

        # --- Batch Gemini Verification for Selected Items ---
        if selected_items:
            batch_prompt = build_batch_evidence_verification_prompt(
                merchant_name=merchant_name,
                merchant_domain=merchant_domain,
                anomaly_type=anomaly_type,
                occurred_at_str=occurred_at_str,
                risk_reason=risk_reason,
                evidence_items=selected_items,
            )

            try:
                logger.info(
                    "Executing single batch Gemini verification for {} evidence items (model: {})",
                    len(selected_items),
                    client._model_name,
                )
                config = types.GenerateContentConfig(
                    system_instruction=VERIFICATION_SYSTEM_INSTRUCTION,
                    response_mime_type="application/json",
                    response_schema=BatchEvidenceVerificationResponse,
                    temperature=0.1,  # Low temperature for deterministic analysis
                )
                response = with_gemini_retry(
                    lambda: client._client.models.generate_content(
                        model=client._model_name,
                        contents=batch_prompt,
                        config=config,
                    ),
                    operation_name=f"verify_batch_{investigation_id}",
                )

                raw_text = response.text.strip() if response.text else "{}"
                parsed = json.loads(raw_text)
                batch_response = BatchEvidenceVerificationResponse.model_validate(parsed)

                # Index returned verifications by evidence_id
                returned_by_id = {v.evidence_id: v for v in batch_response.verifications}

                for idx, ev in enumerate(selected_items):
                    item_eval = returned_by_id.get(ev.evidence_id)
                    if not item_eval and idx < len(batch_response.verifications):
                        # Fallback to positional mapping if model altered UUID string
                        item_eval = batch_response.verifications[idx]

                    if item_eval:
                        verified_item = item_eval.model_copy(
                            update={
                                "evidence_id": ev.evidence_id,
                                "status": VerificationStatus.VERIFIED,
                                "failure_reason": None,
                            }
                        )
                    else:
                        verified_item = EvidenceVerificationItem(
                            evidence_id=ev.evidence_id,
                            status=VerificationStatus.FAILED,
                            failure_reason="Omitted from batch response",
                            merchant_match=MerchantMatchLevel.UNCERTAIN,
                            temporal_match=TemporalMatchLevel.UNCERTAIN,
                            explanation_support=ExplanationSupportLevel.UNCERTAIN,
                            evidence_strength=EvidenceStrength.WEAK_CIRCUMSTANTIAL,
                            source_credibility=SourceCredibilityLevel.UNKNOWN,
                            reasoning_summary="Evidence was omitted from Gemini batch response payload.",
                        )

                    all_verification_items.append(verified_item)

                    if verified_item.status == VerificationStatus.VERIFIED:
                        for c in verified_item.contradictions_identified:
                            if c.strip():
                                all_contradictions.add(c.strip())
                        for u in verified_item.uncertainties_noted:
                            if u.strip():
                                all_uncertainties.add(u.strip())

                logger.info("Batch verification completed for {} items", len(selected_items))

            except Exception as e:
                logger.error(
                    "Gemini batch verification failed for investigation {}: {}. Marking selected items as FAILED.",
                    investigation_id,
                    str(e),
                )
                # Fail gracefully: mark all selected items as FAILED without crashing the pipeline
                for ev in selected_items:
                    failed_item = EvidenceVerificationItem(
                        evidence_id=ev.evidence_id,
                        status=VerificationStatus.FAILED,
                        failure_reason=str(e),
                        merchant_match=MerchantMatchLevel.UNCERTAIN,
                        temporal_match=TemporalMatchLevel.UNCERTAIN,
                        explanation_support=ExplanationSupportLevel.UNCERTAIN,
                        evidence_strength=EvidenceStrength.WEAK_CIRCUMSTANTIAL,
                        source_credibility=SourceCredibilityLevel.UNKNOWN,
                        event_category=None,
                        key_facts=[],
                        contradictions_identified=[],
                        uncertainties_noted=[f"Verification failed: {str(e)}"],
                        reasoning_summary=f"Gemini verification failed due to provider error: {str(e)}",
                    )
                    all_verification_items.append(failed_item)

                all_uncertainties.add(f"External evidence verification incomplete due to Gemini provider error: {str(e)}")

        # --- Append SKIPPED items ---
        for ev in skipped_items:
            skipped_item = EvidenceVerificationItem(
                evidence_id=ev.evidence_id,
                status=VerificationStatus.SKIPPED,
                failure_reason=None,
                merchant_match=MerchantMatchLevel.UNCERTAIN,
                temporal_match=TemporalMatchLevel.UNCERTAIN,
                explanation_support=ExplanationSupportLevel.UNCERTAIN,
                evidence_strength=EvidenceStrength.WEAK_CIRCUMSTANTIAL,
                source_credibility=SourceCredibilityLevel.UNKNOWN,
                event_category=None,
                key_facts=[],
                contradictions_identified=[],
                uncertainties_noted=[],
                reasoning_summary=f"Skipped from Gemini verification due to evidence limit threshold (top {limit} selected).",
            )
            all_verification_items.append(skipped_item)

        return VerificationResult(
            investigation_id=investigation_id,
            items=all_verification_items,
            overall_contradictions=list(all_contradictions),
            overall_uncertainties=list(all_uncertainties),
            verified_at_timestamp=datetime.now(timezone.utc).isoformat(),
        )

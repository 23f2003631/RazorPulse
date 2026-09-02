"""
Investigation Orchestrator Service.

Coordinates the end-to-end RazorPulse investigation pipeline:
Risk Event -> Context -> Exa Discovery -> Normalization -> Gemini Verification ->
Deterministic ECI Scoring -> Dossier Synthesis -> Supabase Persistence.
"""

from datetime import datetime, timezone
import json
from typing import Optional
from uuid import UUID

from app.core.exceptions import (
    DatabaseError,
    RazorPulseError,
    ResourceNotFoundError,
)
from app.core.logging import get_logger
from app.repositories import investigation_repository, risk_event_repository
from app.schemas.dossier import EvidenceDossier
from app.schemas.eci import ECIBand, ECIScoreResult
from app.schemas.evidence import NormalizedEvidence
from app.schemas.investigation import (
    InvestigationDetailResponse,
    InvestigationStatus,
)
from app.schemas.verification import EvidenceVerificationItem, VerificationResult
from app.services.exa.search_strategy import ExaSearchStrategy
from app.services.gemini.verifier import GeminiVerifier
from app.services.investigation.dossier_generator import DossierGenerator
from app.services.scoring.eci_engine import ECIEngine

logger = get_logger("investigation_orchestrator")


class InvestigationOrchestrator:
    """
    Executes the end-to-end investigation pipeline.
    """

    def __init__(
        self,
        search_strategy: Optional[ExaSearchStrategy] = None,
        verifier: Optional[GeminiVerifier] = None,
    ):
        self.search_strategy = search_strategy or ExaSearchStrategy()
        self.verifier = verifier or GeminiVerifier()

    def investigate(self, risk_event_id: UUID) -> InvestigationDetailResponse:
        """
        Execute an investigation synchronously for a given risk event.

        Args:
            risk_event_id: UUID of the anomalous risk event to investigate

        Returns:
            InvestigationDetailResponse containing complete dossier, evidence, and scores

        Raises:
            ResourceNotFoundError: If risk event does not exist
            RazorPulseError: If unrecoverable pipeline failure occurs
        """
        logger.info("Starting investigation for risk_event_id={}", risk_event_id)

        # --- Step 1: Load Risk Event and Merchant Context ---
        try:
            risk_event = risk_event_repository.get_by_id(risk_event_id)
        except ResourceNotFoundError:
            raise
        except Exception as e:
            logger.error("Failed to load risk event {}: {}", risk_event_id, str(e))
            raise DatabaseError(f"Failed to load risk event: {e}") from e

        merchant_info = risk_event.get("merchants", {}) or {}
        merchant_name = merchant_info.get("merchant_name") or risk_event.get("merchant_name", "Unknown")
        merchant_domain = merchant_info.get("merchant_domain") or risk_event.get("merchant_domain")
        anomaly_type = risk_event.get("anomaly_type", "transaction_velocity_spike")
        risk_reason = risk_event.get("risk_reason")

        occurred_at_raw = risk_event.get("occurred_at")
        if isinstance(occurred_at_raw, str):
            occurred_at = datetime.fromisoformat(occurred_at_raw)
        elif isinstance(occurred_at_raw, datetime):
            occurred_at = occurred_at_raw
        else:
            occurred_at = None

        # --- Step 2: Create Investigation Record (PENDING) ---
        inv_record = investigation_repository.create(risk_event_id=risk_event_id)
        inv_id = UUID(str(inv_record["id"]))
        current_stage = "INITIALIZATION"

        try:
            # --- Step 3: Search Stage (Exa AI Discovery) ---
            current_stage = "SEARCHING"
            investigation_repository.update_status(inv_id, InvestigationStatus.SEARCHING)

            evidence_items, executed_queries = self.search_strategy.execute_search(
                merchant_name=merchant_name,
                merchant_domain=merchant_domain,
                occurred_at=occurred_at,
                anomaly_type=anomaly_type,
            )
            logger.info("Discovery complete: {} evidence items found", len(evidence_items))

            # --- Step 4: Verification Stage (Gemini Evidence Assessment) ---
            current_stage = "VERIFYING"
            investigation_repository.update_status(inv_id, InvestigationStatus.VERIFYING)

            if evidence_items:
                verification_result = self.verifier.verify_all_evidence(
                    investigation_id=inv_id,
                    evidence_items=evidence_items,
                    merchant_name=merchant_name,
                    merchant_domain=merchant_domain,
                    occurred_at=occurred_at,
                    anomaly_type=anomaly_type,
                    risk_reason=risk_reason,
                )
            else:
                verification_result = VerificationResult(
                    investigation_id=inv_id,
                    items=[],
                    overall_contradictions=[],
                    overall_uncertainties=["No external web evidence found to verify."],
                    verified_at_timestamp=datetime.now(timezone.utc).isoformat(),
                )

            # --- Step 5: Scoring Stage (Deterministic ECI v1) ---
            current_stage = "SCORING"
            investigation_repository.update_status(inv_id, InvestigationStatus.SCORING)

            eci_result = ECIEngine.calculate_eci(
                verification_result=verification_result,
                evidence_items=evidence_items,
            )
            logger.info("ECI calculated: score={}, band={}", eci_result.eci_score, eci_result.band.value)

            # --- Step 6: Dossier Generation ---
            current_stage = "DOSSIER"
            dossier = DossierGenerator.generate_dossier(
                investigation_id=inv_id,
                risk_event=risk_event,
                evidence_items=evidence_items,
                verification_result=verification_result,
                eci_result=eci_result,
                executed_queries=executed_queries,
            )

            # --- Step 7: Supabase Persistence ---
            current_stage = "PERSISTENCE"
            persisted = investigation_repository.update_results(
                investigation_id=inv_id,
                eci_score=eci_result.eci_score,
                eci_band=eci_result.band.value,
                eci_version=eci_result.eci_version,
                evidence_count=len(evidence_items),
                search_queries=executed_queries,
                eci_breakdown=eci_result.model_dump(mode="json"),
                dossier=dossier.model_dump(mode="json"),
                evidence_items=[ev.model_dump(mode="json") for ev in evidence_items],
                verification_items=[item.model_dump(mode="json") for item in verification_result.items],
            )

            # Update status of original risk event to 'completed'
            try:
                risk_event_repository.update_status(risk_event_id, "completed")
            except Exception as e:
                logger.warning("Could not update risk_event status: {}", str(e))

            logger.info("Investigation {} successfully completed and persisted", inv_id)

            return InvestigationDetailResponse(
                id=inv_id,
                risk_event_id=risk_event_id,
                status=InvestigationStatus.COMPLETED,
                eci_score=eci_result.eci_score,
                eci_band=eci_result.band,
                eci_version=eci_result.eci_version,
                evidence_count=len(evidence_items),
                started_at=inv_record.get("started_at"),
                completed_at=persisted.get("completed_at"),
                created_at=inv_record.get("created_at") or datetime.now(timezone.utc),
                updated_at=persisted.get("updated_at"),
                dossier=dossier,
                evidence_items=evidence_items,
                verification_items=verification_result.items,
            )

        except Exception as e:
            logger.error(
                "Investigation {} failed at stage '{}': {}",
                inv_id,
                current_stage,
                str(e),
            )
            try:
                investigation_repository.update_status(
                    investigation_id=inv_id,
                    status=InvestigationStatus.FAILED,
                    error_stage=current_stage,
                    error_message=str(e),
                )
            except Exception as update_err:
                logger.error("Failed to update investigation to FAILED status: {}", str(update_err))

            raise RazorPulseError(f"Investigation failed at stage '{current_stage}': {str(e)}") from e

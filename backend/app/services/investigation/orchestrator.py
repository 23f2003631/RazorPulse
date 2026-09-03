"""
Investigation Orchestrator Service.

Coordinates the end-to-end RazorPulse investigation pipeline:
Risk Event -> Context -> Exa Discovery -> Normalization -> Gemini Verification ->
Deterministic ECI Scoring -> Dossier Synthesis -> Supabase Persistence.
"""

from datetime import datetime, timezone
import json
import time
from typing import Optional
from uuid import UUID

from app.config.settings import get_settings
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
from app.schemas.pipeline_metadata import PipelineMetadata
from app.schemas.verification import (
    EvidenceVerificationItem,
    VerificationResult,
    VerificationStatus,
)
from app.services.evidence_quality import EvidenceQualityService
from app.services.exa.search_strategy import ExaSearchStrategy
from app.services.gemini.prompts import VERIFICATION_PROMPT_VERSION
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
        stage_durations: dict[str, float] = {}
        t0 = time.perf_counter()

        try:
            # --- Step 3: Search Stage (Exa AI Discovery) ---
            current_stage = "SEARCHING"
            investigation_repository.update_status(inv_id, InvestigationStatus.SEARCHING)
            t_stage = time.perf_counter()

            evidence_items, executed_queries = self.search_strategy.execute_search(
                merchant_name=merchant_name,
                merchant_domain=merchant_domain,
                occurred_at=occurred_at,
                anomaly_type=anomaly_type,
            )
            stage_durations["searching"] = round(time.perf_counter() - t_stage, 3)
            logger.info("Discovery complete in {:.3f}s: {} evidence items found", stage_durations["searching"], len(evidence_items))

            # Quality Annotation Gate (advisory annotation, no silent deletion)
            annotated_evidence, quality_summary = EvidenceQualityService.annotate_collection(
                evidence_items=evidence_items,
                merchant_name=merchant_name,
                merchant_domain=merchant_domain,
            )
            logger.info(
                "Quality audit: {} discovered, {} usable, {} flagged, {} claim cluster(s)",
                quality_summary.total_discovered,
                quality_summary.total_usable,
                quality_summary.total_flagged,
                quality_summary.unique_claim_groups,
            )

            # --- Step 4: Verification Stage (Gemini Evidence Assessment) ---
            current_stage = "VERIFYING"
            investigation_repository.update_status(inv_id, InvestigationStatus.VERIFYING)
            t_stage = time.perf_counter()

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
            stage_durations["verifying"] = round(time.perf_counter() - t_stage, 3)
            logger.info("Verification complete in {:.3f}s", stage_durations["verifying"])

            # --- Step 5: Scoring Stage (Deterministic ECI v1.1) ---
            current_stage = "SCORING"
            investigation_repository.update_status(inv_id, InvestigationStatus.SCORING)
            t_stage = time.perf_counter()

            evidence_group_ids = {
                a.evidence.evidence_id: a.evidence_group_id
                for a in annotated_evidence
                if a.evidence_group_id
            }
            eci_result = ECIEngine.calculate_eci(
                verification_result=verification_result,
                evidence_items=evidence_items,
                evidence_group_ids=evidence_group_ids,
            )
            stage_durations["scoring"] = round(time.perf_counter() - t_stage, 3)
            logger.info("ECI calculated in {:.3f}s: score={}, band={}", stage_durations["scoring"], eci_result.eci_score, eci_result.band.value)

            # --- Build Pipeline Reproducibility Metadata ---
            settings = get_settings()
            pipeline_metadata = PipelineMetadata(
                pipeline_version="0.3.0",
                eci_version=eci_result.eci_version,
                search_strategy_version="v1",
                verification_prompt_version=VERIFICATION_PROMPT_VERSION,
                gemini_model=settings.GEMINI_MODEL,
                gemini_max_evidence_items=settings.GEMINI_MAX_EVIDENCE_ITEMS,
                started_at=inv_record.get("started_at") or datetime.now(timezone.utc),
                completed_at=datetime.now(timezone.utc),
                stage_durations=stage_durations,
                query_count=len(executed_queries),
                evidence_discovered_count=len(evidence_items),
                evidence_usable_count=quality_summary.total_usable,
                evidence_verified_count=len([i for i in verification_result.items if getattr(i, "status", None) == VerificationStatus.VERIFIED]),
                evidence_skipped_count=len([i for i in verification_result.items if getattr(i, "status", None) == VerificationStatus.SKIPPED]),
                evidence_failed_count=len([i for i in verification_result.items if getattr(i, "status", None) == VerificationStatus.FAILED]),
                claim_clusters_count=quality_summary.unique_claim_groups,
            )

            # --- Step 6: Dossier Generation ---
            current_stage = "DOSSIER"
            t_stage = time.perf_counter()
            dossier = DossierGenerator.generate_dossier(
                investigation_id=inv_id,
                risk_event=risk_event,
                evidence_items=evidence_items,
                verification_result=verification_result,
                eci_result=eci_result,
                executed_queries=executed_queries,
                pipeline_metadata=pipeline_metadata,
                quality_summary=quality_summary,
            )
            stage_durations["dossier"] = round(time.perf_counter() - t_stage, 3)

            # --- Step 7: Supabase Persistence ---
            current_stage = "PERSISTENCE"
            t_stage = time.perf_counter()
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
            stage_durations["persistence"] = round(time.perf_counter() - t_stage, 3)
            pipeline_metadata.total_duration_seconds = round(time.perf_counter() - t0, 3)
            if dossier.pipeline_metadata:
                dossier.pipeline_metadata.total_duration_seconds = pipeline_metadata.total_duration_seconds

            # Update status of original risk event to 'completed'
            try:
                risk_event_repository.update_status(risk_event_id, "completed")
            except Exception as e:
                logger.warning("Could not update risk_event status: {}", str(e))

            logger.info("Investigation {} successfully completed in {:.3f}s", inv_id, pipeline_metadata.total_duration_seconds)

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
                pipeline_metadata=pipeline_metadata,
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

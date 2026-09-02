"""
End-to-end Integration Tests for Investigation Pipeline.

Tests the full orchestrator execution across all 3 realistic synthetic scenarios.
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from uuid import uuid4
import pytest

from app.schemas.eci import ECIBand
from app.schemas.investigation import InvestigationStatus
from app.schemas.verification import VerificationResult
from app.services.investigation.orchestrator import InvestigationOrchestrator
from tests.fixtures.synthetic_scenarios import (
    SCENARIO_1_EVIDENCE_ITEMS,
    SCENARIO_1_RISK_EVENT,
    SCENARIO_1_VERIFICATIONS,
    SCENARIO_2_EVIDENCE_ITEMS,
    SCENARIO_2_RISK_EVENT,
    SCENARIO_2_VERIFICATIONS,
    SCENARIO_3_EVIDENCE_ITEMS,
    SCENARIO_3_RISK_EVENT,
    SCENARIO_3_VERIFICATIONS,
)


class TestInvestigationPipelineE2E:
    """End-to-end pipeline execution tests."""

    @patch("app.services.investigation.orchestrator.investigation_repository")
    @patch("app.services.investigation.orchestrator.risk_event_repository")
    def test_pipeline_scenario_1_strong_corroboration(self, mock_event_repo, mock_inv_repo):
        """Pipeline should correctly process a strong viral launch event and persist high ECI."""
        inv_id = uuid4()
        event_id = uuid4()

        mock_event_repo.get_by_id.return_value = {**SCENARIO_1_RISK_EVENT, "id": str(event_id)}
        mock_inv_repo.create.return_value = {
            "id": str(inv_id),
            "risk_event_id": str(event_id),
            "status": "pending",
            "started_at": datetime.now(timezone.utc).isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        mock_inv_repo.update_status.return_value = {"id": str(inv_id)}
        mock_inv_repo.update_results.return_value = {
            "id": str(inv_id),
            "status": "completed",
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        # Mock Search Strategy
        mock_search = MagicMock()
        mock_search.execute_search.return_value = (
            SCENARIO_1_EVIDENCE_ITEMS,
            [{"query_text": "q1", "intent": "timeframe_event"}],
        )

        # Mock Verifier
        mock_verifier = MagicMock()
        mock_verifier.verify_all_evidence.return_value = VerificationResult(
            investigation_id=inv_id,
            items=SCENARIO_1_VERIFICATIONS,
            overall_contradictions=[],
            overall_uncertainties=[],
            verified_at_timestamp="now",
        )

        orchestrator = InvestigationOrchestrator(
            search_strategy=mock_search,
            verifier=mock_verifier,
        )

        result = orchestrator.investigate(event_id)

        assert result.id == inv_id
        assert result.status == InvestigationStatus.COMPLETED
        assert result.eci_score >= 60
        assert result.eci_band in (ECIBand.STRONG, ECIBand.VERY_STRONG)
        assert result.evidence_count == 3
        assert result.dossier is not None
        assert len(result.dossier.evidence_citations) == 3

    @patch("app.services.investigation.orchestrator.investigation_repository")
    @patch("app.services.investigation.orchestrator.risk_event_repository")
    def test_pipeline_scenario_2_zero_evidence(self, mock_event_repo, mock_inv_repo):
        """Pipeline should handle zero search results cleanly, producing ECI=0 without failure."""
        inv_id = uuid4()
        event_id = uuid4()

        mock_event_repo.get_by_id.return_value = {**SCENARIO_2_RISK_EVENT, "id": str(event_id)}
        mock_inv_repo.create.return_value = {
            "id": str(inv_id),
            "risk_event_id": str(event_id),
            "status": "pending",
            "started_at": datetime.now(timezone.utc).isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        mock_inv_repo.update_status.return_value = {"id": str(inv_id)}
        mock_inv_repo.update_results.return_value = {
            "id": str(inv_id),
            "status": "completed",
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        mock_search = MagicMock()
        mock_search.execute_search.return_value = ([], [])

        mock_verifier = MagicMock()

        orchestrator = InvestigationOrchestrator(
            search_strategy=mock_search,
            verifier=mock_verifier,
        )

        result = orchestrator.investigate(event_id)

        assert result.status == InvestigationStatus.COMPLETED
        assert result.eci_score == 0
        assert result.eci_band == ECIBand.LOW
        assert result.evidence_count == 0
        assert result.dossier.eci_result.is_zero_evidence is True

    @patch("app.services.investigation.orchestrator.investigation_repository")
    @patch("app.services.investigation.orchestrator.risk_event_repository")
    def test_pipeline_scenario_3_contradicted_event(self, mock_event_repo, mock_inv_repo):
        """Pipeline should detect contradictions and penalize ECI accordingly."""
        inv_id = uuid4()
        event_id = uuid4()

        mock_event_repo.get_by_id.return_value = {**SCENARIO_3_RISK_EVENT, "id": str(event_id)}
        mock_inv_repo.create.return_value = {
            "id": str(inv_id),
            "risk_event_id": str(event_id),
            "status": "pending",
            "started_at": datetime.now(timezone.utc).isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        mock_inv_repo.update_status.return_value = {"id": str(inv_id)}
        mock_inv_repo.update_results.return_value = {
            "id": str(inv_id),
            "status": "completed",
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        mock_search = MagicMock()
        mock_search.execute_search.return_value = (
            SCENARIO_3_EVIDENCE_ITEMS,
            [{"query_text": "q3", "intent": "timeframe_event"}],
        )

        mock_verifier = MagicMock()
        mock_verifier.verify_all_evidence.return_value = VerificationResult(
            investigation_id=inv_id,
            items=SCENARIO_3_VERIFICATIONS,
            overall_contradictions=["Merchant official notice explicitly refutes flash sale."],
            overall_uncertainties=[],
            verified_at_timestamp="now",
        )

        orchestrator = InvestigationOrchestrator(
            search_strategy=mock_search,
            verifier=mock_verifier,
        )

        result = orchestrator.investigate(event_id)

        assert result.status == InvestigationStatus.COMPLETED
        assert result.dossier.contradictions is not None
        assert len(result.dossier.contradictions) == 1
        assert result.dossier.eci_result.penalty_points > 0

    @patch("app.services.investigation.orchestrator.investigation_repository")
    @patch("app.services.investigation.orchestrator.risk_event_repository")
    def test_pipeline_graceful_completion_on_gemini_failure(self, mock_event_repo, mock_inv_repo):
        """Pipeline should complete gracefully with ECI=0 and explicit limitations when Gemini fails."""
        from app.schemas.verification import EvidenceVerificationItem, VerificationStatus
        inv_id = uuid4()
        event_id = uuid4()

        mock_event_repo.get_by_id.return_value = {**SCENARIO_1_RISK_EVENT, "id": str(event_id)}
        mock_inv_repo.create.return_value = {
            "id": str(inv_id),
            "risk_event_id": str(event_id),
            "status": "pending",
            "started_at": datetime.now(timezone.utc).isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        mock_inv_repo.update_status.return_value = {"id": str(inv_id)}
        mock_inv_repo.update_results.return_value = {
            "id": str(inv_id),
            "status": "completed",
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        mock_search = MagicMock()
        mock_search.execute_search.return_value = (
            SCENARIO_1_EVIDENCE_ITEMS,
            [{"query_text": "q1", "intent": "timeframe_event"}],
        )

        mock_verifier = MagicMock()
        failed_items = [
            EvidenceVerificationItem(
                evidence_id=ev.evidence_id,
                status=VerificationStatus.FAILED,
                failure_reason="429 ResourceExhausted: GenerateRequestsPerDay",
                reasoning_summary="Gemini verification failed",
            )
            for ev in SCENARIO_1_EVIDENCE_ITEMS
        ]
        mock_verifier.verify_all_evidence.return_value = VerificationResult(
            investigation_id=inv_id,
            items=failed_items,
            overall_contradictions=[],
            overall_uncertainties=["Gemini provider quota exhausted."],
            verified_at_timestamp="now",
        )

        orchestrator = InvestigationOrchestrator(
            search_strategy=mock_search,
            verifier=mock_verifier,
        )

        result = orchestrator.investigate(event_id)

        assert result.status == InvestigationStatus.COMPLETED
        assert result.eci_score == 0
        assert result.eci_band == ECIBand.LOW
        assert len(result.dossier.evidence_citations) == 0
        assert "Gemini verification could not be completed" in result.dossier.executive_summary
        assert result.dossier.eci_result.is_zero_evidence is True

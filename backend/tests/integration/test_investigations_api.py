"""
Integration tests for Investigations API routes.
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient
import pytest

from app.main import app
from app.schemas.investigation import InvestigationStatus
from tests.fixtures.synthetic_scenarios import (
    SCENARIO_1_EVIDENCE_ITEMS,
    SCENARIO_1_RISK_EVENT,
    SCENARIO_1_VERIFICATIONS,
)

client = TestClient(app)

MOCK_INV_ID = str(uuid4())
MOCK_EVENT_ID = SCENARIO_1_RISK_EVENT["id"]


class TestInvestigationsAPI:
    """Test suite for /api/v1/investigations endpoints."""

    @patch("app.services.investigation.orchestrator.investigation_repository")
    @patch("app.services.investigation.orchestrator.risk_event_repository")
    @patch("app.services.investigation.orchestrator.ExaSearchStrategy")
    @patch("app.services.investigation.orchestrator.GeminiVerifier")
    def test_create_investigation_success(
        self,
        mock_verifier_cls,
        mock_search_cls,
        mock_event_repo,
        mock_inv_repo,
    ):
        """Should trigger and complete an investigation returning 201 with detail response."""
        mock_event_repo.get_by_id.return_value = SCENARIO_1_RISK_EVENT
        mock_inv_repo.create.return_value = {
            "id": MOCK_INV_ID,
            "risk_event_id": MOCK_EVENT_ID,
            "status": "pending",
            "started_at": datetime.now(timezone.utc).isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        mock_inv_repo.update_status.return_value = {"id": MOCK_INV_ID, "status": "scoring"}
        mock_inv_repo.update_results.return_value = {
            "id": MOCK_INV_ID,
            "status": "completed",
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        # Mock search strategy
        mock_search_inst = MagicMock()
        mock_search_inst.execute_search.return_value = (
            SCENARIO_1_EVIDENCE_ITEMS,
            [{"query_text": 'UrbanCraft sale', "intent": "commercial_campaign", "results_count": 3, "status": "success"}],
        )
        mock_search_cls.return_value = mock_search_inst

        # Mock verifier
        mock_verifier_inst = MagicMock()
        from app.schemas.verification import VerificationResult
        mock_verifier_inst.verify_all_evidence.return_value = VerificationResult(
            investigation_id=uuid4(),
            items=SCENARIO_1_VERIFICATIONS,
            overall_contradictions=[],
            overall_uncertainties=[],
            verified_at_timestamp="2026-08-28T15:00:00Z",
        )
        mock_verifier_cls.return_value = mock_verifier_inst

        response = client.post(
            "/api/v1/investigations",
            json={"risk_event_id": MOCK_EVENT_ID},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["id"] == MOCK_INV_ID
        assert data["risk_event_id"] == MOCK_EVENT_ID
        assert data["status"] == "completed"
        assert data["eci_score"] is not None
        assert data["dossier"] is not None
        assert data["dossier"]["anomaly_context"]["merchant_name"] == "UrbanCraft India"
        assert len(data["evidence_items"]) == 3

    def test_create_investigation_invalid_uuid(self):
        """Should return 422 for invalid risk_event_id format."""
        response = client.post(
            "/api/v1/investigations",
            json={"risk_event_id": "not-a-valid-uuid"},
        )
        assert response.status_code == 422

    @patch("app.services.investigation.orchestrator.risk_event_repository")
    def test_create_investigation_nonexistent_event(self, mock_event_repo):
        """Should return 404 when risk event is not found."""
        from app.core.exceptions import ResourceNotFoundError
        mock_event_repo.get_by_id.side_effect = ResourceNotFoundError("risk_event", str(uuid4()))

        response = client.post(
            "/api/v1/investigations",
            json={"risk_event_id": str(uuid4())},
        )
        assert response.status_code == 404

    @patch("app.api.routes.investigations.investigation_repository")
    def test_get_investigation_success(self, mock_inv_repo):
        """Should return investigation details by ID."""
        mock_inv_repo.get_by_id.return_value = {
            "id": MOCK_INV_ID,
            "risk_event_id": MOCK_EVENT_ID,
            "status": "completed",
            "eci_score": 82,
            "eci_band": "very_strong",
            "eci_version": "v1",
            "evidence_count": 3,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "dossier": None,
            "evidence_items": [],
            "verification_items": [],
        }

        response = client.get(f"/api/v1/investigations/{MOCK_INV_ID}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == MOCK_INV_ID
        assert data["eci_score"] == 82
        assert data["eci_band"] == "very_strong"

    @patch("app.api.routes.investigations.investigation_repository")
    def test_get_investigation_not_found(self, mock_inv_repo):
        """Should return 404 for nonexistent investigation ID."""
        from app.core.exceptions import ResourceNotFoundError
        mock_inv_repo.get_by_id.side_effect = ResourceNotFoundError("investigation", str(uuid4()))

        response = client.get(f"/api/v1/investigations/{uuid4()}")
        assert response.status_code == 404

    @patch("app.api.routes.investigations.investigation_repository")
    def test_list_investigations(self, mock_inv_repo):
        """Should return paginated list of investigations."""
        mock_inv_repo.list_investigations.return_value = (
            [
                {
                    "id": MOCK_INV_ID,
                    "risk_event_id": MOCK_EVENT_ID,
                    "status": "completed",
                    "eci_score": 82,
                    "eci_band": "very_strong",
                    "eci_version": "v1",
                    "evidence_count": 3,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
            ],
            1,
        )

        response = client.get("/api/v1/investigations?limit=10&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert len(data["data"]) == 1
        assert data["data"][0]["id"] == MOCK_INV_ID

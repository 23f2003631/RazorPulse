"""
Integration tests for risk event endpoints.

Tests the risk event ingestion and retrieval endpoints.
Uses mocked Supabase client to avoid requiring a live database.
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import app
from tests.fixtures.risk_events import VIRAL_SPIKE_EVENT

client = TestClient(app)


# Mock merchant record returned from Supabase
MOCK_MERCHANT = {
    "id": str(uuid4()),
    "merchant_name": "UrbanCraft India",
    "merchant_domain": "urbancraft.in",
    "created_at": datetime.now(timezone.utc).isoformat(),
}

# Mock risk event record returned from Supabase
MOCK_RISK_EVENT_ID = str(uuid4())
MOCK_RISK_EVENT = {
    "id": MOCK_RISK_EVENT_ID,
    "merchant_id": MOCK_MERCHANT["id"],
    "anomaly_type": "transaction_velocity_spike",
    "occurred_at": "2026-08-28T14:30:00+05:30",
    "baseline_transaction_count": 85,
    "observed_transaction_count": 1450,
    "percentage_change": 1605.88,
    "transaction_amount": 725000.00,
    "currency": "INR",
    "risk_reason": "Transaction velocity increased 17x above baseline.",
    "geographic_info": "Bengaluru, Karnataka, IN",
    "source": "simulated",
    "status": "pending",
    "created_at": datetime.now(timezone.utc).isoformat(),
    "updated_at": None,
}


class TestCreateRiskEvent:
    """Test suite for POST /api/v1/risk-events."""

    @patch("app.services.risk_event_service.risk_event_repository")
    @patch("app.services.risk_event_service.merchant_repository")
    def test_create_risk_event_success(self, mock_merchant_repo, mock_event_repo):
        """Should successfully create a risk event with valid input."""
        mock_merchant_repo.find_or_create.return_value = MOCK_MERCHANT
        mock_event_repo.create.return_value = MOCK_RISK_EVENT

        response = client.post("/api/v1/risk-events", json=VIRAL_SPIKE_EVENT)

        assert response.status_code == 201
        data = response.json()
        assert data["merchant_name"] == "UrbanCraft India"
        assert data["anomaly_type"] == "transaction_velocity_spike"
        assert data["status"] == "pending"
        assert data["source"] == "simulated"

    def test_create_risk_event_missing_merchant_name(self):
        """Should reject event without merchant_name (422)."""
        invalid_event = {
            "anomaly_type": "transaction_velocity_spike",
            "occurred_at": "2026-08-28T14:30:00+05:30",
        }
        response = client.post("/api/v1/risk-events", json=invalid_event)
        assert response.status_code == 422

    def test_create_risk_event_invalid_anomaly_type(self):
        """Should reject event with invalid anomaly_type (422)."""
        invalid_event = {
            "merchant_name": "Test",
            "anomaly_type": "invalid_type",
            "occurred_at": "2026-08-28T14:30:00+05:30",
        }
        response = client.post("/api/v1/risk-events", json=invalid_event)
        assert response.status_code == 422

    def test_create_risk_event_empty_body(self):
        """Should reject empty request body (422)."""
        response = client.post("/api/v1/risk-events", json={})
        assert response.status_code == 422


class TestGetRiskEvent:
    """Test suite for GET /api/v1/risk-events/{event_id}."""

    @patch("app.services.risk_event_service.risk_event_repository")
    def test_get_risk_event_success(self, mock_event_repo):
        """Should return risk event by ID."""
        mock_event_with_merchant = {
            **MOCK_RISK_EVENT,
            "merchants": {
                "merchant_name": "UrbanCraft India",
                "merchant_domain": "urbancraft.in",
            },
        }
        mock_event_repo.get_by_id.return_value = mock_event_with_merchant

        response = client.get(f"/api/v1/risk-events/{MOCK_RISK_EVENT_ID}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == MOCK_RISK_EVENT_ID

    def test_get_risk_event_invalid_uuid(self):
        """Should return 422 for invalid UUID."""
        response = client.get("/api/v1/risk-events/not-a-uuid")
        assert response.status_code == 422


class TestListRiskEvents:
    """Test suite for GET /api/v1/risk-events."""

    @patch("app.services.risk_event_service.risk_event_repository")
    def test_list_risk_events_empty(self, mock_event_repo):
        """Should return empty list when no events exist."""
        mock_event_repo.list_events.return_value = ([], 0)

        response = client.get("/api/v1/risk-events")
        assert response.status_code == 200
        data = response.json()
        assert data["data"] == []
        assert data["count"] == 0

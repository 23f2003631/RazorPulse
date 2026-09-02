"""
Unit tests for Pydantic schema validation.

Tests that risk event and merchant schemas correctly validate
input data, including boundary conditions and invalid data.
"""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.schemas.risk_event import (
    AnomalyType,
    EventSource,
    RiskEventCreate,
    RiskEventStatus,
)


class TestRiskEventCreate:
    """Test suite for RiskEventCreate schema validation."""

    def test_valid_minimal_event(self):
        """Should accept a minimal valid risk event."""
        event = RiskEventCreate(
            merchant_name="Test Merchant",
            anomaly_type=AnomalyType.TRANSACTION_VELOCITY_SPIKE,
            occurred_at=datetime.now(timezone.utc),
        )
        assert event.merchant_name == "Test Merchant"
        assert event.anomaly_type == AnomalyType.TRANSACTION_VELOCITY_SPIKE
        assert event.currency == "INR"  # default
        assert event.source == EventSource.SIMULATED  # default

    def test_valid_full_event(self):
        """Should accept a fully populated risk event."""
        event = RiskEventCreate(
            merchant_name="UrbanCraft India",
            merchant_domain="urbancraft.in",
            anomaly_type=AnomalyType.TRANSACTION_VELOCITY_SPIKE,
            occurred_at=datetime(2026, 8, 28, 14, 30, tzinfo=timezone.utc),
            baseline_transaction_count=85,
            observed_transaction_count=1450,
            transaction_amount=725000.00,
            currency="INR",
            risk_reason="17x velocity spike",
            geographic_info="Bengaluru, Karnataka, IN",
            source=EventSource.SIMULATED,
        )
        assert event.merchant_domain == "urbancraft.in"
        assert event.baseline_transaction_count == 85
        assert event.observed_transaction_count == 1450

    def test_percentage_change_calculation(self):
        """Should correctly calculate percentage change."""
        event = RiskEventCreate(
            merchant_name="Test",
            anomaly_type=AnomalyType.VOLUME_SURGE,
            occurred_at=datetime.now(timezone.utc),
            baseline_transaction_count=100,
            observed_transaction_count=1200,
        )
        assert event.percentage_change == 1100.0

    def test_percentage_change_zero_baseline(self):
        """Should return None when baseline is zero."""
        event = RiskEventCreate(
            merchant_name="Test",
            anomaly_type=AnomalyType.VOLUME_SURGE,
            occurred_at=datetime.now(timezone.utc),
            baseline_transaction_count=0,
            observed_transaction_count=100,
        )
        assert event.percentage_change is None

    def test_percentage_change_missing_values(self):
        """Should return None when baseline or observed is missing."""
        event = RiskEventCreate(
            merchant_name="Test",
            anomaly_type=AnomalyType.VOLUME_SURGE,
            occurred_at=datetime.now(timezone.utc),
        )
        assert event.percentage_change is None

    def test_currency_uppercase(self):
        """Currency should be normalized to uppercase."""
        event = RiskEventCreate(
            merchant_name="Test",
            anomaly_type=AnomalyType.OTHER,
            occurred_at=datetime.now(timezone.utc),
            currency="inr",
        )
        assert event.currency == "INR"

    def test_invalid_missing_merchant_name(self):
        """Should reject event without merchant_name."""
        with pytest.raises(ValidationError) as exc_info:
            RiskEventCreate(
                anomaly_type=AnomalyType.TRANSACTION_VELOCITY_SPIKE,
                occurred_at=datetime.now(timezone.utc),
            )
        assert "merchant_name" in str(exc_info.value)

    def test_invalid_empty_merchant_name(self):
        """Should reject event with empty merchant_name."""
        with pytest.raises(ValidationError):
            RiskEventCreate(
                merchant_name="",
                anomaly_type=AnomalyType.TRANSACTION_VELOCITY_SPIKE,
                occurred_at=datetime.now(timezone.utc),
            )

    def test_invalid_missing_anomaly_type(self):
        """Should reject event without anomaly_type."""
        with pytest.raises(ValidationError):
            RiskEventCreate(
                merchant_name="Test",
                occurred_at=datetime.now(timezone.utc),
            )

    def test_invalid_negative_transaction_count(self):
        """Should reject negative transaction counts."""
        with pytest.raises(ValidationError):
            RiskEventCreate(
                merchant_name="Test",
                anomaly_type=AnomalyType.VOLUME_SURGE,
                occurred_at=datetime.now(timezone.utc),
                baseline_transaction_count=-10,
            )

    def test_invalid_negative_transaction_amount(self):
        """Should reject negative transaction amounts."""
        with pytest.raises(ValidationError):
            RiskEventCreate(
                merchant_name="Test",
                anomaly_type=AnomalyType.VOLUME_SURGE,
                occurred_at=datetime.now(timezone.utc),
                transaction_amount=-100.0,
            )

    def test_all_anomaly_types_valid(self):
        """All enum values should be accepted."""
        for anomaly_type in AnomalyType:
            event = RiskEventCreate(
                merchant_name="Test",
                anomaly_type=anomaly_type,
                occurred_at=datetime.now(timezone.utc),
            )
            assert event.anomaly_type == anomaly_type

    def test_all_event_sources_valid(self):
        """All event source values should be accepted."""
        for source in EventSource:
            event = RiskEventCreate(
                merchant_name="Test",
                anomaly_type=AnomalyType.OTHER,
                occurred_at=datetime.now(timezone.utc),
                source=source,
            )
            assert event.source == source


class TestRiskEventStatus:
    """Test suite for RiskEventStatus enum."""

    def test_all_statuses_exist(self):
        """All expected statuses should be defined."""
        expected = {"pending", "investigating", "completed", "failed", "dismissed"}
        actual = {s.value for s in RiskEventStatus}
        assert expected == actual

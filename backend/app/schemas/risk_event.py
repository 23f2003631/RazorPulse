"""
Risk Event Pydantic schemas.

A RiskEvent is the central domain object in RazorPulse.
It represents an anomalous payment pattern that requires investigation.

IMPORTANT DISTINCTION:
  RiskEvent ≠ Payment/Transaction
  A RiskEvent captures an ANOMALY (e.g., velocity spike) that may span
  many individual transactions. RazorPulse investigates whether external
  evidence explains the anomaly.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class AnomalyType(str, Enum):
    """
    Types of payment anomalies that RazorPulse can investigate.

    These are categories of anomalous behaviour, not Razorpay
    API event types. They are used internally by RazorPulse.
    """

    TRANSACTION_VELOCITY_SPIKE = "transaction_velocity_spike"
    TRANSACTION_AMOUNT_SPIKE = "transaction_amount_spike"
    NEW_GEOGRAPHY = "new_geography"
    UNUSUAL_PATTERN = "unusual_pattern"
    VOLUME_SURGE = "volume_surge"
    OTHER = "other"


class RiskEventStatus(str, Enum):
    """
    Investigation lifecycle status for a risk event.
    """

    PENDING = "pending"           # Ingested, not yet investigated
    INVESTIGATING = "investigating"  # Exa/Gemini pipeline running
    COMPLETED = "completed"       # Investigation finished, ECI available
    FAILED = "failed"             # Investigation pipeline error
    DISMISSED = "dismissed"       # Analyst dismissed (no action needed)


class EventSource(str, Enum):
    """
    Origin of the risk event data.

    Clearly distinguishes REAL Razorpay data from SIMULATED test data.
    This distinction is essential for honest reporting.
    """

    SIMULATED = "simulated"       # Synthetic test data
    RAZORPAY_WEBHOOK = "razorpay_webhook"  # Real Razorpay webhook
    RAZORPAY_API = "razorpay_api"          # Polled from Razorpay API
    MANUAL = "manual"             # Analyst-created manual event


class RiskEventCreate(BaseModel):
    """
    Schema for creating a new risk event via the ingestion endpoint.

    This represents the input payload when a simulated or real
    risk signal is received.
    """

    # --- Merchant identification ---
    merchant_name: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Name of the merchant experiencing the anomaly",
        examples=["ExampleBrand"],
    )
    merchant_domain: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Merchant's web domain (critical for Exa search)",
        examples=["example.com"],
    )

    # --- Anomaly characterization ---
    anomaly_type: AnomalyType = Field(
        ...,
        description="Category of the observed anomaly",
        examples=["transaction_velocity_spike"],
    )
    occurred_at: datetime = Field(
        ...,
        description="When the anomaly was detected or began",
    )

    # --- Quantitative signals ---
    baseline_transaction_count: Optional[int] = Field(
        default=None,
        ge=0,
        description="Normal/expected transaction count for this period",
        examples=[100],
    )
    observed_transaction_count: Optional[int] = Field(
        default=None,
        ge=0,
        description="Actual transaction count during the anomaly",
        examples=[1200],
    )
    transaction_amount: Optional[float] = Field(
        default=None,
        ge=0,
        description="Total transaction amount during the anomaly (in minor units or currency amount)",
        examples=[450000.00],
    )
    currency: str = Field(
        default="INR",
        max_length=3,
        description="ISO 4217 currency code",
        examples=["INR"],
    )

    # --- Context ---
    risk_reason: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Human-readable description of why this is flagged",
        examples=["Unusual transaction velocity — 12x baseline"],
    )
    geographic_info: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Geographic context if available (city, state, country)",
        examples=["Mumbai, Maharashtra, IN"],
    )

    # --- Source ---
    source: EventSource = Field(
        default=EventSource.SIMULATED,
        description="Origin of this risk event data. SIMULATED for synthetic test data.",
    )

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        return v.upper()

    @property
    def percentage_change(self) -> Optional[float]:
        """Calculate percentage change from baseline, if both values are provided."""
        if (
            self.baseline_transaction_count is not None
            and self.observed_transaction_count is not None
            and self.baseline_transaction_count > 0
        ):
            return round(
                ((self.observed_transaction_count - self.baseline_transaction_count)
                 / self.baseline_transaction_count) * 100,
                2,
            )
        return None


class RiskEventResponse(BaseModel):
    """
    Schema for risk event data returned from the API.
    """

    id: UUID
    merchant_id: UUID
    merchant_name: str
    merchant_domain: Optional[str] = None

    anomaly_type: AnomalyType
    occurred_at: datetime

    baseline_transaction_count: Optional[int] = None
    observed_transaction_count: Optional[int] = None
    percentage_change: Optional[float] = None
    transaction_amount: Optional[float] = None
    currency: str

    risk_reason: Optional[str] = None
    geographic_info: Optional[str] = None

    source: EventSource
    status: RiskEventStatus

    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class RiskEventListResponse(BaseModel):
    """Response schema for listing risk events."""

    data: list[RiskEventResponse]
    count: int

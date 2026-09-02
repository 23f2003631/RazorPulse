"""
Merchant Pydantic schemas.

Merchants are entities whose transaction anomalies are being
investigated. A merchant record is created or updated when a
risk event is ingested.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl


class MerchantBase(BaseModel):
    """Shared merchant fields."""

    merchant_name: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Display name of the merchant",
        examples=["ExampleBrand"],
    )
    merchant_domain: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Primary web domain of the merchant (used for Exa search)",
        examples=["example.com"],
    )


class MerchantCreate(MerchantBase):
    """Schema for creating a new merchant (internal use)."""

    pass


class MerchantResponse(MerchantBase):
    """Schema for merchant data returned from the API."""

    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

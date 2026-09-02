"""
Exa AI service schemas.

Pydantic models for Exa search request/response validation.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ExaSearchRequest(BaseModel):
    """Request parameters for an Exa search."""

    merchant_name: str = Field(..., description="Merchant name to search for")
    merchant_domain: Optional[str] = Field(None, description="Merchant domain for search refinement")
    anomaly_date: Optional[datetime] = Field(None, description="Date of the anomaly for temporal filtering")
    num_results: int = Field(default=10, ge=1, le=50, description="Max results to return")


class ExaResultItem(BaseModel):
    """A single Exa search result."""

    title: Optional[str] = None
    url: str
    published_date: Optional[str] = None
    author: Optional[str] = None
    score: Optional[float] = None
    text: Optional[str] = None
    highlights: Optional[list[str]] = None


class ExaSearchResultResponse(BaseModel):
    """Response from an Exa search."""

    results: list[ExaResultItem]
    query: str
    result_count: int

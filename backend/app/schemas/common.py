"""
Common Pydantic schemas shared across the application.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Response schema for the health check endpoint."""

    status: str
    app: str
    version: str
    environment: str


class ErrorResponse(BaseModel):
    """Standard error response schema."""

    error: str
    message: str
    details: Optional[dict] = None


class PaginatedResponse(BaseModel):
    """Wrapper for paginated list responses."""

    data: list
    count: int
    limit: int
    offset: int

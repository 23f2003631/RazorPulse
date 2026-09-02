"""
Risk Events API routes.

POST /api/v1/risk-events        — Ingest a simulated risk event
GET  /api/v1/risk-events        — List risk events
GET  /api/v1/risk-events/{id}   — Get a risk event by ID

These endpoints handle SIMULATED risk events for prototype development.
Real Razorpay risk webhooks would be integrated here in a future phase
if a suitable public webhook event exists.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query

from app.core.exceptions import (
    DatabaseError,
    ResourceNotFoundError,
    RiskEventValidationError,
)
from app.core.logging import get_logger
from app.schemas.risk_event import (
    RiskEventCreate,
    RiskEventListResponse,
    RiskEventResponse,
)
from app.services import risk_event_service

logger = get_logger("risk_events_route")

router = APIRouter(prefix="/api/v1/risk-events", tags=["risk-events"])


@router.post("", response_model=RiskEventResponse, status_code=201)
async def create_risk_event(event_input: RiskEventCreate):
    """
    Ingest a new risk event.

    Accepts a simulated or manually-created risk anomaly event,
    validates it, normalizes it, and persists it.

    The event is stored with status 'pending' and is NOT automatically
    sent to the investigation pipeline (Exa/Gemini) in this phase.

    NOTE: This endpoint accepts SIMULATED risk data for prototype
    development. Source field honestly tracks data provenance.
    """
    try:
        result = risk_event_service.ingest_risk_event(event_input)
        return result
    except RiskEventValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except DatabaseError as e:
        logger.error("Database error during risk event ingestion: {}", str(e))
        raise HTTPException(status_code=503, detail="Database service unavailable")
    except Exception as e:
        logger.error("Unexpected error during risk event ingestion: {}", str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{event_id}", response_model=RiskEventResponse)
async def get_risk_event(event_id: UUID):
    """
    Retrieve a specific risk event by ID.
    """
    try:
        return risk_event_service.get_risk_event(event_id)
    except ResourceNotFoundError:
        raise HTTPException(status_code=404, detail=f"Risk event not found: {event_id}")
    except DatabaseError as e:
        logger.error("Database error fetching risk event: {}", str(e))
        raise HTTPException(status_code=503, detail="Database service unavailable")


@router.get("", response_model=RiskEventListResponse)
async def list_risk_events(
    limit: int = Query(default=50, ge=1, le=100, description="Results per page"),
    offset: int = Query(default=0, ge=0, description="Pagination offset"),
    status: Optional[str] = Query(default=None, description="Filter by status"),
):
    """
    List risk events with optional filtering and pagination.
    """
    try:
        events, total_count = risk_event_service.list_risk_events(
            limit=limit,
            offset=offset,
            status=status,
        )
        return RiskEventListResponse(data=events, count=total_count)
    except DatabaseError as e:
        logger.error("Database error listing risk events: {}", str(e))
        raise HTTPException(status_code=503, detail="Database service unavailable")

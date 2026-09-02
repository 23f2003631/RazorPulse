"""
Investigations API routes.

POST /api/v1/investigations        — Trigger an investigation for a risk event
GET  /api/v1/investigations/{id}   — Get full investigation details & dossier
GET  /api/v1/investigations        — List investigations with filtering
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query

from app.core.exceptions import (
    DatabaseError,
    RazorPulseError,
    ResourceNotFoundError,
)
from app.core.logging import get_logger
from app.repositories import investigation_repository
from app.schemas.dossier import EvidenceDossier
from app.schemas.evidence import NormalizedEvidence
from app.schemas.investigation import (
    InvestigationCreate,
    InvestigationDetailResponse,
    InvestigationListResponse,
    InvestigationResponse,
    InvestigationStatus,
)
from app.schemas.verification import EvidenceVerificationItem
from app.services.investigation.orchestrator import InvestigationOrchestrator

logger = get_logger("investigations_route")

router = APIRouter(prefix="/api/v1/investigations", tags=["investigations"])


@router.post("", response_model=InvestigationDetailResponse, status_code=201)
async def create_investigation(request: InvestigationCreate):
    """
    Trigger an external-context investigation for a specified risk anomaly event.

    Executes the complete investigation pipeline synchronously:
    1. Loads risk event context
    2. Generates search query intents
    3. Discovers external evidence via Exa AI
    4. Evaluates evidence validity via Google Gemini
    5. Calculates deterministic ECI score (v1 heuristic)
    6. Synthesizes human-readable Evidence Dossier
    7. Persists full results to database

    Returns the completed InvestigationDetailResponse with dossier.
    """
    try:
        orchestrator = InvestigationOrchestrator()
        result = orchestrator.investigate(risk_event_id=request.risk_event_id)
        return result
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"Risk event not found: {request.risk_event_id}")
    except DatabaseError as e:
        logger.error("Database error during investigation creation: {}", str(e))
        raise HTTPException(status_code=503, detail="Database service unavailable")
    except RazorPulseError as e:
        logger.error("Pipeline failure during investigation: {}", str(e))
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error("Unexpected error during investigation: {}", str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{investigation_id}", response_model=InvestigationDetailResponse)
async def get_investigation(investigation_id: UUID):
    """
    Retrieve full investigation details, including complete Evidence Dossier
    and verified citations.
    """
    try:
        inv = investigation_repository.get_by_id(investigation_id)

        dossier_data = inv.get("dossier")
        dossier = EvidenceDossier.model_validate(dossier_data) if dossier_data else None

        evidence_items_data = inv.get("evidence_items") or []
        evidence_items = [NormalizedEvidence.model_validate(item) for item in evidence_items_data]

        verification_items_data = inv.get("verification_items") or []
        verification_items = [EvidenceVerificationItem.model_validate(item) for item in verification_items_data]

        return InvestigationDetailResponse(
            id=inv["id"],
            risk_event_id=inv["risk_event_id"],
            status=inv["status"],
            eci_score=inv.get("eci_score"),
            eci_band=inv.get("eci_band"),
            eci_version=inv.get("eci_version", "v1"),
            evidence_count=inv.get("evidence_count", 0),
            error_stage=inv.get("error_stage"),
            error_message=inv.get("error_message"),
            started_at=inv.get("started_at"),
            completed_at=inv.get("completed_at"),
            created_at=inv["created_at"],
            updated_at=inv.get("updated_at"),
            dossier=dossier,
            evidence_items=evidence_items,
            verification_items=verification_items,
        )
    except ResourceNotFoundError:
        raise HTTPException(status_code=404, detail=f"Investigation not found: {investigation_id}")
    except DatabaseError as e:
        logger.error("Database error fetching investigation: {}", str(e))
        raise HTTPException(status_code=503, detail="Database service unavailable")


@router.get("", response_model=InvestigationListResponse)
async def list_investigations(
    limit: int = Query(default=50, ge=1, le=100, description="Results per page"),
    offset: int = Query(default=0, ge=0, description="Pagination offset"),
    status: Optional[str] = Query(default=None, description="Filter by investigation status"),
    risk_event_id: Optional[UUID] = Query(default=None, description="Filter by risk event ID"),
):
    """
    List investigations with optional status and risk event filtering.
    """
    try:
        records, total_count = investigation_repository.list_investigations(
            limit=limit,
            offset=offset,
            status=status,
            risk_event_id=risk_event_id,
        )

        items = [
            InvestigationResponse(
                id=r["id"],
                risk_event_id=r["risk_event_id"],
                status=r["status"],
                eci_score=r.get("eci_score"),
                eci_band=r.get("eci_band"),
                eci_version=r.get("eci_version", "v1"),
                evidence_count=r.get("evidence_count", 0),
                error_stage=r.get("error_stage"),
                error_message=r.get("error_message"),
                started_at=r.get("started_at"),
                completed_at=r.get("completed_at"),
                created_at=r["created_at"],
                updated_at=r.get("updated_at"),
            )
            for r in records
        ]

        return InvestigationListResponse(data=items, count=total_count)
    except DatabaseError as e:
        logger.error("Database error listing investigations: {}", str(e))
        raise HTTPException(status_code=503, detail="Database service unavailable")

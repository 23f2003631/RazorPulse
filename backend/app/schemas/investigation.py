"""
Investigation domain schemas.

Manages the lifecycle of an external-context investigation in RazorPulse.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.dossier import EvidenceDossier
from app.schemas.eci import ECIBand, ECIScoreResult
from app.schemas.evidence import NormalizedEvidence
from app.schemas.verification import EvidenceVerificationItem


class InvestigationStatus(str, Enum):
    """
    Lifecycle status of an investigation.
    """

    PENDING = "pending"         # Created, waiting to start
    SEARCHING = "searching"     # Executing Exa external search
    VERIFYING = "verifying"     # Running Gemini evidence verification
    SCORING = "scoring"         # Calculating deterministic ECI
    COMPLETED = "completed"     # Successfully finished with dossier
    FAILED = "failed"           # Pipeline error encountered


class InvestigationCreate(BaseModel):
    """
    Request payload to trigger an investigation.

    Minimal, clean contract: client supplies the risk_event_id.
    Merchant and anomaly context are resolved automatically from the event.
    """

    risk_event_id: UUID = Field(
        ...,
        description="UUID of the existing risk event to investigate",
    )


class InvestigationResponse(BaseModel):
    """
    Summary representation of an investigation.
    """

    id: UUID
    risk_event_id: UUID
    status: InvestigationStatus
    eci_score: Optional[int] = None
    eci_band: Optional[ECIBand] = None
    eci_version: str = "v1"
    evidence_count: int = 0
    error_stage: Optional[str] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class InvestigationDetailResponse(BaseModel):
    """
    Full investigation response including complete Evidence Dossier,
    normalized evidence items, and verification outputs.
    """

    id: UUID
    risk_event_id: UUID
    status: InvestigationStatus
    eci_score: Optional[int] = None
    eci_band: Optional[ECIBand] = None
    eci_version: str = "v1"
    evidence_count: int = 0
    error_stage: Optional[str] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    # Full artifacts
    dossier: Optional[EvidenceDossier] = None
    evidence_items: list[NormalizedEvidence] = Field(default_factory=list)
    verification_items: list[EvidenceVerificationItem] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class InvestigationListResponse(BaseModel):
    """Paginated list of investigations."""
    data: list[InvestigationResponse]
    count: int

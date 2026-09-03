"""
Evidence Dossier schemas.

The Evidence Dossier is the primary deliverable of an investigation.
It synthesizes the risk anomaly context, discovered evidence, verification verdicts,
deterministic ECI score breakdown, and analyst guidance.

IMPORTANT:
  The dossier is a decision-support document for a human risk analyst.
  It does not make autonomous risk decisions, approve/reject merchants,
  or unfreeze accounts.
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.eci import ECIScoreResult
from app.schemas.evidence import NormalizedEvidence
from app.schemas.pipeline_metadata import PipelineMetadata
from app.schemas.verification import EvidenceVerificationItem


class AnomalySummary(BaseModel):
    """Snapshot of the investigated risk anomaly."""
    risk_event_id: UUID
    merchant_name: str
    merchant_domain: Optional[str] = None
    anomaly_type: str
    occurred_at: datetime
    baseline_transaction_count: Optional[int] = None
    observed_transaction_count: Optional[int] = None
    percentage_change: Optional[float] = None
    transaction_amount: Optional[float] = None
    currency: str = "INR"
    risk_reason: Optional[str] = None
    geographic_info: Optional[str] = None


class EvidenceCitation(BaseModel):
    """Citations linking verified facts to specific evidence items."""
    citation_id: str = Field(..., description="Citation marker (e.g. [E1])")
    evidence_id: UUID = Field(..., description="Referenced evidence ID")
    url: str = Field(..., description="Source URL")
    title: Optional[str] = None
    source_domain: str
    source_type: str
    key_fact: str
    temporal_match: str
    source_credibility: str


class EvidenceDossier(BaseModel):
    """
    Comprehensive Evidence Dossier synthesized for the human risk analyst.
    """

    investigation_id: UUID = Field(..., description="Unique investigation identifier")
    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when dossier was generated",
    )
    pipeline_version: str = Field(default="0.3.0", description="Pipeline build version")
    eci_version: str = Field(default="v1", description="ECI heuristic engine version")
    pipeline_metadata: Optional[PipelineMetadata] = Field(
        default=None,
        description="Detailed reproducibility and performance metadata",
    )

    # --- Section 1: Anomaly Context ---
    anomaly_context: AnomalySummary = Field(..., description="Anomaly details")

    # --- Section 2: Executive Summary ---
    executive_summary: str = Field(
        ...,
        description="Human-readable synthesis of investigation findings",
    )

    # --- Section 3: Corroboration Outcome ---
    eci_result: ECIScoreResult = Field(
        ...,
        description="Deterministic ECI score, band, and itemized factor contributions",
    )

    # --- Section 4: Evidence & Citations ---
    evidence_count: int = Field(..., description="Total evidence items discovered and processed")
    evidence_citations: list[EvidenceCitation] = Field(
        default_factory=list,
        description="Traceable citations to discovered source material",
    )

    # --- Section 5: Unresolved Concerns & Discrepancies ---
    contradictions: list[str] = Field(
        default_factory=list,
        description="Discrepancies or conflicting statements identified across sources",
    )
    evidence_gaps: list[str] = Field(
        default_factory=list,
        description="Missing context or unconfirmed details in the external record",
    )
    verification_uncertainties: list[str] = Field(
        default_factory=list,
        description="Ambiguities or unverified claims noted during assessment",
    )

    # --- Section 6: Analyst Guidance ---
    analyst_review_checklist: list[str] = Field(
        default_factory=list,
        description="Recommended verification steps for the human analyst",
    )

    # --- Section 7: Search Provenance ---
    search_queries_used: list[dict] = Field(
        default_factory=list,
        description="Queries executed with intent categories and timestamp",
    )

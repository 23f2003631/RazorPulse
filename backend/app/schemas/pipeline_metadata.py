"""
Pipeline Reproducibility & Observability Metadata Schema.

Captures comprehensive operational provenance for an investigation run:
pipeline versions, prompt versions, model configurations, stage timings,
and evidence processing counts.

Enables full historical auditability and reproducibility across runs.
"""

from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field


class PipelineMetadata(BaseModel):
    """
    Structured reproducibility and performance metadata for an investigation.

    Persisted in Supabase and included in Evidence Dossier / API responses.
    """

    # Version Tracking
    pipeline_version: str = Field(
        default="0.3.0",
        description="RazorPulse overall pipeline build version",
    )
    eci_version: str = Field(
        default="v1",
        description="Deterministic ECI scoring formula version",
    )
    search_strategy_version: str = Field(
        default="v1",
        description="Exa search query intent builder and strategy version",
    )
    verification_prompt_version: str = Field(
        default="v1",
        description="Gemini verification prompt template version",
    )
    gemini_model: str = Field(
        ...,
        description="Exact model identifier used for evidence verification",
    )
    gemini_max_evidence_items: int = Field(
        default=4,
        description="Configured cap for Gemini verification items",
    )

    # Execution Timings
    started_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when investigation began",
    )
    completed_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp when investigation finalized",
    )
    total_duration_seconds: Optional[float] = Field(
        default=None,
        description="Total end-to-end execution duration in seconds",
    )
    stage_durations: dict[str, float] = Field(
        default_factory=dict,
        description="Individual stage durations in seconds: searching, verifying, scoring, dossier, persistence",
    )

    # Counts & Statistics
    query_count: int = Field(
        default=0,
        description="Total search queries executed",
    )
    evidence_discovered_count: int = Field(
        default=0,
        description="Total raw external evidence items discovered",
    )
    evidence_usable_count: int = Field(
        default=0,
        description="Evidence items passing quality gates",
    )
    evidence_verified_count: int = Field(
        default=0,
        description="Evidence items successfully verified by Gemini (status=VERIFIED)",
    )
    evidence_skipped_count: int = Field(
        default=0,
        description="Evidence items skipped due to max items threshold (status=SKIPPED)",
    )
    evidence_failed_count: int = Field(
        default=0,
        description="Evidence items where verification failed (status=FAILED)",
    )
    claim_clusters_count: int = Field(
        default=0,
        description="Distinct claim/content clusters identified during quality annotation",
    )

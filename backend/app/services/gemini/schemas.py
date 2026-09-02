"""
Gemini evidence verification schemas.

Pydantic models for the structured output that Gemini will produce
when verifying external evidence against a risk anomaly.

NOTE: These are PRELIMINARY schemas for Day 1 connectivity testing.
The full verification schema will be designed during the scoring/evaluation
phase when the ECI engine is implemented.
"""

from typing import Optional

from pydantic import BaseModel, Field


class EvidenceRelevanceAssessment(BaseModel):
    """
    Gemini's structured assessment of evidence relevance.

    This schema will be used as the response_schema for Gemini's
    structured output mode in the full verification pipeline.

    IMPORTANT: This assessment is an INPUT to the deterministic
    scoring engine, not the final risk decision.
    """

    entity_match: bool = Field(
        description="Does the evidence reference the same merchant/entity?"
    )
    temporal_relevance: float = Field(
        ge=0.0,
        le=1.0,
        description="How temporally close is the event to the anomaly? (0=irrelevant, 1=exact match)",
    )
    event_type: Optional[str] = Field(
        default=None,
        description="Type of external event (e.g., viral_social_media, press_coverage, product_launch)",
    )
    relevance_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Overall relevance of this evidence to the anomaly (0=irrelevant, 1=highly relevant)",
    )
    explanation: str = Field(
        description="Brief explanation of why this evidence is or isn't relevant",
    )
    contradictions: Optional[str] = Field(
        default=None,
        description="Any contradictions found in the evidence",
    )
    source_credibility: float = Field(
        ge=0.0,
        le=1.0,
        description="Estimated credibility of the evidence source (0=unreliable, 1=highly credible)",
    )

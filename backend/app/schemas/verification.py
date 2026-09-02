"""
Gemini Evidence Verification schemas.

Pydantic models for structured verification output produced by Gemini.
Strictly grounded in supplied evidence text — no hallucinations, no autonomous risk decisions.
"""

from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class MerchantMatchLevel(str, Enum):
    """How directly the evidence identifies the merchant."""
    DIRECT_MATCH = "direct_match"        # Explicitly names merchant / merchant domain
    RELATED_ENTITY = "related_entity"    # Parent company, subsidiary, co-brand partner
    UNRELATED = "unrelated"              # Refers to a different entity
    UNCERTAIN = "uncertain"              # Ambiguous or insufficient information


class TemporalMatchLevel(str, Enum):
    """How temporally aligned the evidence is with the anomaly."""
    EXACT_MATCH = "exact_match"                # Within 0-48 hours of anomaly timestamp
    WINDOW_MATCH = "window_match"              # Within 7 days of anomaly (active window)
    HISTORICAL_PREVIOUS = "historical_previous"# Past event (weeks/months prior)
    POST_ANOMALY = "post_anomaly"              # Occurred significantly after anomaly
    UNRELATED_TIMING = "unrelated_timing"      # Different timeframe entirely
    UNCERTAIN = "uncertain"                    # Date unknown / cannot be determined


class ExplanationSupportLevel(str, Enum):
    """
    How strongly the evidence supports an explanation for the transaction anomaly.

    NOTE: This evaluates whether the supplied text describes a surge-inducing event
    (e.g. product launch, viral campaign, flash sale, press feature), NOT whether
    the merchant is 'good' or 'safe'.
    """
    STRONG_EXPLANATION = "strong_explanation"    # Clear, direct explanation for surge
    MODERATE_EXPLANATION = "moderate_explanation"# Plausible contributing context
    WEAK_EXPLANATION = "weak_explanation"        # Minor or tangential mention
    NO_EXPLANATION = "no_explanation"            # Does not explain anomalous activity
    UNCERTAIN = "uncertain"                      # Cannot determine from text


class EvidenceStrength(str, Enum):
    """Directness and evidentiary strength of the source content."""
    STRONG_DIRECT = "strong_direct"              # Primary source, official statement, verified news
    MODERATE_INDIRECT = "moderate_indirect"      # Secondary reporting, industry summary
    WEAK_CIRCUMSTANTIAL = "weak_circumstantial"  # User comment, indirect rumor, aggregator
    UNSUPPORTED = "unsupported"                  # Claim made without backing detail
    CONTRADICTED = "contradicted"                # Source explicitly refutes the event


class SourceCredibilityLevel(str, Enum):
    """Assessed credibility of the source for this specific claim."""
    HIGH = "high"        # Recognized news outlet, verified official channel
    MEDIUM = "medium"    # Established blog, trade portal, verified account
    LOW = "low"          # Unverified blog, user forum, anonymous post
    UNKNOWN = "unknown"  # Cannot ascertain credibility from snippet


class EvidenceVerificationItem(BaseModel):
    """
    Structured verification assessment of a single evidence item.

    Produced by Gemini using response_schema enforcement.
    """

    evidence_id: UUID = Field(
        ...,
        description="ID of the evidence item being evaluated (provenance link)",
    )
    merchant_match: MerchantMatchLevel = Field(
        ...,
        description="Assessment of entity identity match",
    )
    temporal_match: TemporalMatchLevel = Field(
        ...,
        description="Assessment of temporal alignment with anomaly occurred_at",
    )
    explanation_support: ExplanationSupportLevel = Field(
        ...,
        description="Assessment of how well evidence explains the surge anomaly",
    )
    evidence_strength: EvidenceStrength = Field(
        ...,
        description="Directness and evidentiary strength of the source content",
    )
    source_credibility: SourceCredibilityLevel = Field(
        ...,
        description="Assessed credibility level of the reporting source",
    )
    event_category: Optional[str] = Field(
        default=None,
        description="Category of external event (e.g., product_launch, viral_campaign, flash_sale, press_feature)",
    )
    key_facts: list[str] = Field(
        default_factory=list,
        description="Factual claims directly stated in the evidence text (no hallucinations)",
    )
    contradictions_identified: list[str] = Field(
        default_factory=list,
        description="Any factual contradictions or discrepancies noted in the text",
    )
    uncertainties_noted: list[str] = Field(
        default_factory=list,
        description="Missing information or ambiguities noted in the text",
    )
    reasoning_summary: str = Field(
        ...,
        description="Concise synthesis explaining the verification assessment",
    )


class VerificationResult(BaseModel):
    """
    Aggregated verification results for all evidence items in an investigation.
    """

    investigation_id: UUID = Field(..., description="Investigation ID")
    items: list[EvidenceVerificationItem] = Field(
        default_factory=list,
        description="Individual evidence item assessments",
    )
    overall_contradictions: list[str] = Field(
        default_factory=list,
        description="Consolidated list of cross-evidence contradictions",
    )
    overall_uncertainties: list[str] = Field(
        default_factory=list,
        description="Consolidated list of unresolved uncertainties and evidence gaps",
    )
    verified_at_timestamp: str = Field(..., description="ISO timestamp of verification")

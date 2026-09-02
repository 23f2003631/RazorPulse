"""
Event Corroboration Index (ECI) schemas.

Represents the deterministic scoring engine output and factor contributions.
Adheres strictly to the ECI v1 heuristic methodology.

IMPORTANT DISCLAIMER:
  The ECI measures the strength of external evidence corroborating
  a real-world explanation for a transaction anomaly.
  It is NOT a risk score and does NOT indicate whether a merchant is safe or fraudulent.
"""

from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ECIBand(str, Enum):
    """
    Qualitative bands for the Event Corroboration Index.

    These are heuristic descriptive labels for external corroboration strength,
    NOT merchant risk classifications.
    """

    LOW = "low"                   # 0–29: Low External Corroboration
    MODERATE = "moderate"         # 30–59: Moderate External Corroboration
    STRONG = "strong"             # 60–79: Strong External Corroboration
    VERY_STRONG = "very_strong"   # 80–100: Very Strong External Corroboration


class ECIFactorCategory(str, Enum):
    """Category of ECI score factor."""
    ENTITY_MATCH = "entity_match"
    TEMPORAL_ALIGNMENT = "temporal_alignment"
    EXPLANATION_SUPPORT = "explanation_support"
    SOURCE_CREDIBILITY = "source_credibility"
    INDEPENDENT_CORROBORATION = "independent_corroboration"
    CONTRADICTION_PENALTY = "contradiction_penalty"
    UNCERTAINTY_PENALTY = "uncertainty_penalty"


class ECIFactorContribution(BaseModel):
    """
    Detailed, transparent breakdown of a single factor's contribution to the ECI.
    """

    factor_id: str = Field(..., description="Unique identifier for the factor rule")
    category: ECIFactorCategory = Field(..., description="Orthogonal factor category")
    name: str = Field(..., description="Human-readable factor title")
    raw_value: str = Field(..., description="Underlying attribute value evaluated")
    points_awarded: float = Field(..., description="Points added or deducted (positive or negative)")
    max_possible_points: float = Field(..., description="Maximum possible points for this dimension")
    explanation: str = Field(..., description="Clear explanation of why this point value was assigned")
    evidence_ids: list[UUID] = Field(
        default_factory=list,
        description="IDs of evidence items that contributed to this factor evaluation",
    )


class ECIScoreResult(BaseModel):
    """
    Complete deterministic ECI evaluation output.
    """

    eci_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Event Corroboration Index bounded between 0 and 100",
    )
    band: ECIBand = Field(..., description="Qualitative corroboration band")
    band_label: str = Field(
        ...,
        description="Descriptive text label (e.g., 'Strong External Corroboration')",
    )
    confidence_level: str = Field(
        ...,
        description="Confidence in evaluation (HIGH, MEDIUM, LOW) based on evidence density and clarity",
    )
    eci_version: str = Field(
        default="v1",
        description="Version identifier of the ECI scoring engine formula",
    )
    positive_points: float = Field(..., description="Sum of positive corroborating points before penalties")
    penalty_points: float = Field(..., description="Total deduction points from contradictions and uncertainties")
    factors: list[ECIFactorContribution] = Field(
        default_factory=list,
        description="Complete itemized list of factor contributions",
    )
    is_zero_evidence: bool = Field(
        default=False,
        description="Flag indicating that zero external evidence was discovered",
    )
    disclaimer: str = Field(
        default=(
            "The Event Corroboration Index (ECI) measures the strength of external evidence "
            "corroborating a legitimate contextual explanation for an observed anomaly. "
            "It does NOT represent a fraud determination, account clearance, or risk decision."
        ),
        description="Standard mandatory product disclaimer",
    )

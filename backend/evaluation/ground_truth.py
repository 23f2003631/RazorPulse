"""
Evaluation Ground Truth Model.

Defines the evaluation schema for RazorPulse benchmark cases.

IMPORTANT DESIGN DECISIONS:
1. CorroborationClass and ContradictionState are INDEPENDENT dimensions.
   ECI measures corroboration strength. Contradiction is a separate evidence property.
2. Ground truth labels describe the EXPECTED EVIDENCE STATE, not ECI scores.
   ECI scores are CALCULATED and then COMPARED against ground truth — never used as tuning targets.
3. ECI band ↔ corroboration mapping is a documented classification policy,
   not a definitional identity.

CLASSIFICATION POLICY (documented, not tuned):
  ECI 0        → NO_CORROBORATION
  ECI 1–29     → WEAK_CORROBORATION
  ECI 30–59    → MODERATE_CORROBORATION
  ECI 60–100   → STRONG_CORROBORATION

Contradiction detection is evaluated separately as a binary classification.
"""

from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.evidence import NormalizedEvidence
from app.schemas.verification import EvidenceVerificationItem


class CorroborationClass(str, Enum):
    """
    Ground-truth corroboration strength label.

    These describe the EXPECTED evidence state, independent of ECI score.
    """
    STRONG_CORROBORATION = "strong_corroboration"
    MODERATE_CORROBORATION = "moderate_corroboration"
    WEAK_CORROBORATION = "weak_corroboration"
    NO_CORROBORATION = "no_corroboration"


class ContradictionState(str, Enum):
    """
    Ground-truth contradiction presence label.

    Independent from corroboration class — a case can have strong corroboration
    AND a contradiction present.
    """
    CONTRADICTION_PRESENT = "contradiction_present"
    CONTRADICTION_ABSENT = "contradiction_absent"


class DifficultyLevel(str, Enum):
    """Difficulty classification for benchmark stratification."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class DatasetSplit(str, Enum):
    """Dataset partition for evaluation integrity."""
    DEVELOPMENT = "development"
    HELD_OUT = "held_out"


class EvalCase(BaseModel):
    """
    A single evaluation case for the RazorPulse benchmark.

    Contains all inputs (evidence fixtures, verification fixtures) and
    expected ground-truth labels needed to evaluate the deterministic
    ECI engine without any external API calls.

    Ground truth labels are INDEPENDENT from ECI scores:
    - expected_corroboration: describes the evidence state
    - expected_contradiction: describes contradiction presence
    - ECI scores are CALCULATED and COMPARED, never used as targets
    """

    # --- Case Identity ---
    case_id: str = Field(..., description="Unique case identifier (e.g. 'A01_strong_viral_campaign')")
    archetype: str = Field(..., description="Scenario archetype letter (A–L) from evaluation design")
    description: str = Field(..., description="Human-readable description of what this case tests")
    difficulty: DifficultyLevel = Field(..., description="Difficulty classification")
    split: DatasetSplit = Field(..., description="Development or held-out partition")

    # --- Merchant & Anomaly Context ---
    merchant_name: str
    merchant_domain: str
    anomaly_type: str = "transaction_velocity_spike"
    occurred_at: str = Field(..., description="ISO timestamp of anomaly")
    baseline_transaction_count: int = 100
    observed_transaction_count: int = 500
    percentage_change: float = 400.0
    currency: str = "INR"
    risk_reason: str = ""
    geographic_info: Optional[str] = None

    # --- Evidence Fixtures ---
    evidence_items: list[NormalizedEvidence] = Field(
        default_factory=list,
        description="Pre-built normalized evidence items (synthetic, not from live Exa)",
    )

    # --- Verification Fixtures ---
    verification_items: list[EvidenceVerificationItem] = Field(
        default_factory=list,
        description="Pre-built verification assessments (synthetic, not from live Gemini)",
    )
    overall_contradictions: list[str] = Field(
        default_factory=list,
        description="Contradictions that would be aggregated in VerificationResult",
    )
    overall_uncertainties: list[str] = Field(
        default_factory=list,
        description="Uncertainties that would be aggregated in VerificationResult",
    )

    # --- Ground Truth Labels (INDEPENDENT from ECI) ---
    expected_corroboration: CorroborationClass = Field(
        ...,
        description="Expected corroboration class based on the evidence state",
    )
    expected_contradiction: ContradictionState = Field(
        default=ContradictionState.CONTRADICTION_ABSENT,
        description="Expected contradiction detection state",
    )

    # --- Contextual Hypothesis ---
    contextual_hypothesis: str = Field(
        default="",
        description="What real-world scenario this case simulates and what it tests",
    )


# =============================================================================
# ECI → Corroboration Classification Policy
# =============================================================================
# This is a DOCUMENTED MAPPING, not a definitional identity.
# It converts ECI integer scores to the 4-class corroboration taxonomy.

def eci_to_corroboration_class(eci_score: int) -> CorroborationClass:
    """
    Map an ECI score to a corroboration class using the documented classification policy.

    Policy:
        0        → NO_CORROBORATION
        1–29     → WEAK_CORROBORATION
        30–59    → MODERATE_CORROBORATION
        60–100   → STRONG_CORROBORATION

    This is a measurement transformation, NOT a ground-truth definition.
    """
    if eci_score == 0:
        return CorroborationClass.NO_CORROBORATION
    elif eci_score <= 29:
        return CorroborationClass.WEAK_CORROBORATION
    elif eci_score <= 59:
        return CorroborationClass.MODERATE_CORROBORATION
    else:
        return CorroborationClass.STRONG_CORROBORATION


def has_contradiction_detected(contradictions: list[str]) -> bool:
    """
    Determine if contradictions were detected in the verification output.

    This is the system's binary contradiction detection output,
    compared independently against the ground-truth ContradictionState.
    """
    return len(contradictions) > 0

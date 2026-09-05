"""
Deterministic Demo Scenarios for RazorPulse.

Provides 3 realistic, reproducible demonstration scenarios showcasing
different external evidence profiles:

1. DEMO_STRONG: Legitimate commercial campaign with multi-source verified evidence.
   Semantic expectation: Strong external corroboration; aligned entity and timeframe.
2. DEMO_ZERO: Unexplained velocity spike with zero discoverable external evidence.
   Semantic expectation: No external corroboration; clean zero-evidence state.
3. DEMO_CONTRADICTED: Anomalous surge where credible evidence includes explicit contradiction.
   Semantic expectation: Contradiction identified; evidence discrepancy flagged for analyst.

CRITICAL USER INSTRUCTION:
Demo scenarios are NOT tuned or hard-coded to reach predetermined ECI scores.
They reflect realistic evidence fixtures, and the runner reports the exact ECI
and factor breakdown computed by the engine.
"""

from dataclasses import dataclass, field
from typing import Optional
from uuid import UUID, uuid4

from app.schemas.dossier import EvidenceDossier
from app.schemas.eci import ECIScoreResult
from app.schemas.evidence import NormalizedEvidence
from app.schemas.verification import EvidenceVerificationItem, VerificationResult
from app.services.investigation.dossier_generator import DossierGenerator
from app.services.scoring.eci_engine import ECIEngine
from evaluation.dataset import (
    CASE_A01,  # UrbanCraft India viral product launch
    CASE_D01,  # QuickDeal Bazaar unexplained spike
    CASE_H01,  # TrendWear Daily official refutation / duplicate glitch
)
from evaluation.ground_truth import EvalCase


@dataclass
class DemoScenarioResult:
    """Result of running a demo scenario through the offline pipeline."""
    scenario_name: str
    scenario_title: str
    semantic_expectation: str
    merchant_name: str
    anomaly_summary: str
    evidence_count: int
    eci_score: int
    eci_band: str
    factors_summary: list[dict]
    contradictions: list[str]
    analyst_checklist: list[str]
    dossier: EvidenceDossier
    evidence_items: list[NormalizedEvidence] = field(default_factory=list)
    verification_items: list[EvidenceVerificationItem] = field(default_factory=list)


def run_demo_case(
    eval_case: EvalCase,
    scenario_name: str,
    scenario_title: str,
    semantic_expectation: str,
) -> DemoScenarioResult:
    scenario_uuids = {
        "demo_strong": (
            UUID("11111111-1111-4111-8111-111111111111"),
            "10000000-0000-4000-8000-000000000001",
        ),
        "demo_zero": (
            UUID("22222222-2222-4222-8222-222222222222"),
            "20000000-0000-4000-8000-000000000002",
        ),
        "demo_contradicted": (
            UUID("33333333-3333-4333-8333-333333333333"),
            "30000000-0000-4000-8000-000000000003",
        ),
    }
    inv_id, evt_id = scenario_uuids.get(scenario_name, (uuid4(), str(uuid4())))
    investigation_id = inv_id
    evidence_items = eval_case.evidence_items
    verification_items = list(eval_case.verification_items)

    # Sync IDs between evidence and verifications
    for i, (ev, vi) in enumerate(zip(evidence_items, verification_items)):
        verification_items[i] = vi.model_copy(update={"evidence_id": ev.evidence_id})

    verification_result = VerificationResult(
        investigation_id=investigation_id,
        items=verification_items,
        overall_contradictions=eval_case.overall_contradictions,
        overall_uncertainties=eval_case.overall_uncertainties,
        verified_at_timestamp="2026-09-01T12:00:00Z",
    )

    eci_result = ECIEngine.calculate_eci(
        verification_result=verification_result,
        evidence_items=evidence_items,
    )

    risk_event_dict = {
        "id": evt_id,
        "merchant_name": eval_case.merchant_name,
        "merchant_domain": eval_case.merchant_domain,
        "anomaly_type": eval_case.anomaly_type,
        "occurred_at": eval_case.occurred_at,
        "baseline_transaction_count": eval_case.baseline_transaction_count,
        "observed_transaction_count": eval_case.observed_transaction_count,
        "percentage_change": eval_case.percentage_change,
        "risk_reason": eval_case.risk_reason,
        "geographic_info": eval_case.geographic_info,
        "currency": eval_case.currency,
    }

    dummy_queries = [
        {"intent": "timeframe_event", "query_text": f'"{eval_case.merchant_name}" news'},
        {"intent": "merchant_announcement", "query_text": f"site:{eval_case.merchant_domain} launch"},
    ]

    dossier = DossierGenerator.generate_dossier(
        investigation_id=investigation_id,
        risk_event=risk_event_dict,
        evidence_items=evidence_items,
        verification_result=verification_result,
        eci_result=eci_result,
        executed_queries=dummy_queries,
    )

    factors_summary = [
        {
            "category": f.category.value,
            "points": f.points_awarded,
            "max": f.max_possible_points,
            "explanation": f.explanation,
        }
        for f in eci_result.factors
    ]

    return DemoScenarioResult(
        scenario_name=scenario_name,
        scenario_title=scenario_title,
        semantic_expectation=semantic_expectation,
        merchant_name=eval_case.merchant_name,
        anomaly_summary=f"{eval_case.percentage_change:.0f}% velocity spike ({eval_case.observed_transaction_count} txns vs {eval_case.baseline_transaction_count} baseline)",
        evidence_count=len(evidence_items),
        eci_score=eci_result.eci_score,
        eci_band=eci_result.band.value,
        factors_summary=factors_summary,
        contradictions=verification_result.overall_contradictions,
        analyst_checklist=dossier.analyst_review_checklist,
        dossier=dossier,
        evidence_items=evidence_items,
        verification_items=verification_items,
    )


def get_demo_scenarios() -> list[DemoScenarioResult]:
    """Run all 3 deterministic demo scenarios and return results."""
    return [
        run_demo_case(
            eval_case=CASE_A01,
            scenario_name="demo_strong",
            scenario_title="Demo 1: Legitimate Festive Surge (UrbanCraft India)",
            semantic_expectation="Strong external corroboration with aligned entity, timing, and credible independent news coverage.",
        ),
        run_demo_case(
            eval_case=CASE_D01,
            scenario_name="demo_zero",
            scenario_title="Demo 2: Unexplained Velocity Spike (QuickDeal Bazaar)",
            semantic_expectation="Zero external evidence found; clean zero-evidence state directing analyst to internal review.",
        ),
        run_demo_case(
            eval_case=CASE_H01,
            scenario_name="demo_contradicted",
            scenario_title="Demo 3: Disputed Commercial Claim (TrendWear Daily)",
            semantic_expectation="Contradiction identified; official merchant notice refutes active flash sale, citing duplicate technical glitch.",
        ),
    ]

"""
Unit tests for Evidence Dossier Generator.
"""

from uuid import uuid4
import pytest

from app.schemas.eci import ECIBand, ECIScoreResult
from app.services.investigation.dossier_generator import DossierGenerator
from app.services.scoring.eci_engine import ECIEngine
from tests.fixtures.synthetic_scenarios import (
    SCENARIO_1_EVIDENCE_ITEMS,
    SCENARIO_1_RISK_EVENT,
    SCENARIO_1_VERIFICATIONS,
    SCENARIO_2_EVIDENCE_ITEMS,
    SCENARIO_2_RISK_EVENT,
    SCENARIO_2_VERIFICATIONS,
    SCENARIO_3_EVIDENCE_ITEMS,
    SCENARIO_3_RISK_EVENT,
    SCENARIO_3_VERIFICATIONS,
)
from app.schemas.verification import VerificationResult


class TestDossierGenerator:
    """Test suite for DossierGenerator."""

    def test_generate_dossier_scenario_1_strong(self):
        """Should assemble a complete dossier with citations and neutral language for Scenario 1."""
        inv_id = uuid4()
        v_res = VerificationResult(
            investigation_id=inv_id,
            items=SCENARIO_1_VERIFICATIONS,
            overall_contradictions=[],
            overall_uncertainties=[],
            verified_at_timestamp="2026-08-28T15:00:00Z",
        )
        eci_res = ECIEngine.calculate_eci(v_res, SCENARIO_1_EVIDENCE_ITEMS)

        dossier = DossierGenerator.generate_dossier(
            investigation_id=inv_id,
            risk_event=SCENARIO_1_RISK_EVENT,
            evidence_items=SCENARIO_1_EVIDENCE_ITEMS,
            verification_result=v_res,
            eci_result=eci_res,
            executed_queries=[{"query_text": 'UrbanCraft sale', "intent": "commercial_campaign"}],
        )

        assert dossier.investigation_id == inv_id
        assert dossier.anomaly_context.merchant_name == "UrbanCraft India"
        assert len(dossier.evidence_citations) == 3
        assert dossier.evidence_citations[0].citation_id == "[E1]"
        assert "UrbanCraft India" in dossier.executive_summary
        assert len(dossier.analyst_review_checklist) >= 2
        assert "red flags" not in dossier.executive_summary.lower()

    def test_generate_dossier_scenario_2_zero_evidence(self):
        """Should cleanly handle zero evidence without errors and state low external corroboration."""
        inv_id = uuid4()
        v_res = VerificationResult(
            investigation_id=inv_id,
            items=SCENARIO_2_VERIFICATIONS,
            overall_contradictions=[],
            overall_uncertainties=["No external web evidence found to verify."],
            verified_at_timestamp="2026-08-30T03:00:00Z",
        )
        eci_res = ECIEngine.calculate_eci(v_res, SCENARIO_2_EVIDENCE_ITEMS)

        dossier = DossierGenerator.generate_dossier(
            investigation_id=inv_id,
            risk_event=SCENARIO_2_RISK_EVENT,
            evidence_items=SCENARIO_2_EVIDENCE_ITEMS,
            verification_result=v_res,
            eci_result=eci_res,
            executed_queries=[],
        )

        assert dossier.investigation_id == inv_id
        assert dossier.evidence_count == 0
        assert len(dossier.evidence_citations) == 0
        assert "No relevant public external web evidence" in dossier.executive_summary
        assert dossier.eci_result.eci_score == 0
        assert len(dossier.evidence_gaps) >= 1

    def test_generate_dossier_scenario_3_contradictions(self):
        """Should highlight specific contradictions and guidance in dossier."""
        inv_id = uuid4()
        v_res = VerificationResult(
            investigation_id=inv_id,
            items=SCENARIO_3_VERIFICATIONS,
            overall_contradictions=["Merchant official notice explicitly refutes that a flash sale is occurring."],
            overall_uncertainties=[],
            verified_at_timestamp="2026-08-29T19:00:00Z",
        )
        eci_res = ECIEngine.calculate_eci(v_res, SCENARIO_3_EVIDENCE_ITEMS)

        dossier = DossierGenerator.generate_dossier(
            investigation_id=inv_id,
            risk_event=SCENARIO_3_RISK_EVENT,
            evidence_items=SCENARIO_3_EVIDENCE_ITEMS,
            verification_result=v_res,
            eci_result=eci_res,
            executed_queries=[],
        )

        assert len(dossier.contradictions) == 1
        assert "refutes" in dossier.contradictions[0]
        # Checklist should prompt checking the discrepancy
        assert any("discrepancy" in item.lower() for item in dossier.analyst_review_checklist)

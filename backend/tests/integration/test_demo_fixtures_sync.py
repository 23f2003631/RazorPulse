"""
Test suite validating synchronization between backend demo scenarios
and frontend offline distribution snapshot.
"""

import json
from pathlib import Path

from app.schemas.investigation import (
    DemoScenarioListResponse,
    DemoScenarioResponse,
)
from evaluation.demo_scenarios import get_demo_scenarios


class TestDemoFixturesSync:
    """Verifies that the offline frontend fixture matches the backend source of truth."""

    def test_fixture_file_exists(self):
        root_dir = Path(__file__).resolve().parent.parent.parent.parent
        fixture_path = root_dir / "frontend" / "src" / "data" / "demoScenariosFixture.json"
        assert fixture_path.exists(), f"Missing offline fixture at {fixture_path}"

    def test_fixture_matches_backend_scenarios(self):
        root_dir = Path(__file__).resolve().parent.parent.parent.parent
        fixture_path = root_dir / "frontend" / "src" / "data" / "demoScenariosFixture.json"

        with open(fixture_path, "r", encoding="utf-8") as f:
            fixture_data = json.load(f)

        assert "scenarios" in fixture_data
        scenarios = fixture_data["scenarios"]
        assert len(scenarios) == 3

        demos = get_demo_scenarios()
        backend_scenarios = [
            DemoScenarioResponse(
                scenario_name=d.scenario_name,
                scenario_title=d.scenario_title,
                semantic_expectation=d.semantic_expectation,
                merchant_name=d.merchant_name,
                anomaly_summary=d.anomaly_summary,
                evidence_count=d.evidence_count,
                eci_score=d.eci_score,
                eci_band=d.eci_band,
                factors_summary=d.factors_summary,
                contradictions=d.contradictions,
                analyst_checklist=d.analyst_checklist,
                dossier=d.dossier,
                evidence_items=d.evidence_items,
                verification_items=d.verification_items,
            )
            for d in demos
        ]
        backend_data = DemoScenarioListResponse(scenarios=backend_scenarios).model_dump(mode="json")

        for f_scen, b_scen in zip(scenarios, backend_data["scenarios"]):
            assert f_scen["scenario_name"] == b_scen["scenario_name"]
            assert f_scen["merchant_name"] == b_scen["merchant_name"]
            assert f_scen["eci_score"] == b_scen["eci_score"]
            assert f_scen["eci_band"] == b_scen["eci_band"]
            assert f_scen["evidence_count"] == b_scen["evidence_count"]
            assert len(f_scen["dossier"]["evidence_citations"]) == len(b_scen["dossier"]["evidence_citations"])
            assert len(f_scen["contradictions"]) == len(b_scen["contradictions"])

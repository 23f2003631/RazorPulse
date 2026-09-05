"""
Integration tests for Demo Scenarios API route.
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestDemoScenariosAPI:
    """Test suite for GET /api/v1/investigations/demo-scenarios endpoint."""

    def test_get_demo_scenarios_success(self):
        """Should return all 3 deterministic demo scenarios without external network calls."""
        response = client.get("/api/v1/investigations/demo-scenarios")
        assert response.status_code == 200

        data = response.json()
        assert "scenarios" in data
        scenarios = data["scenarios"]
        assert len(scenarios) == 3

        names = [s["scenario_name"] for s in scenarios]
        assert "demo_strong" in names
        assert "demo_zero" in names
        assert "demo_contradicted" in names

    def test_demo_strong_structure(self):
        """Demo Strong must have complete dossier, factor breakdown, and citations."""
        response = client.get("/api/v1/investigations/demo-scenarios")
        assert response.status_code == 200

        scenarios = {s["scenario_name"]: s for s in response.json()["scenarios"]}
        s1 = scenarios["demo_strong"]

        assert s1["merchant_name"] == "UrbanCraft India"
        assert s1["eci_score"] == 100
        assert s1["eci_band"] == "very_strong"
        assert s1["evidence_count"] == 3
        assert len(s1["factors_summary"]) > 0
        assert len(s1["dossier"]["evidence_citations"]) > 0
        assert len(s1["evidence_items"]) == 3
        assert len(s1["verification_items"]) == 3

    def test_demo_zero_structure(self):
        """Demo Zero must reflect clean zero-evidence state."""
        response = client.get("/api/v1/investigations/demo-scenarios")
        assert response.status_code == 200

        scenarios = {s["scenario_name"]: s for s in response.json()["scenarios"]}
        s2 = scenarios["demo_zero"]

        assert s2["merchant_name"] == "QuickDeal Bazaar"
        assert s2["eci_score"] == 0
        assert s2["eci_band"] == "low"
        assert s2["evidence_count"] == 0
        assert len(s2["dossier"]["evidence_citations"]) == 0
        assert len(s2["evidence_items"]) == 0

    def test_demo_contradicted_structure(self):
        """Demo Contradicted must flag contradictions and display penalized ECI."""
        response = client.get("/api/v1/investigations/demo-scenarios")
        assert response.status_code == 200

        scenarios = {s["scenario_name"]: s for s in response.json()["scenarios"]}
        s3 = scenarios["demo_contradicted"]

        assert s3["merchant_name"] == "TrendWear Daily"
        assert s3["eci_score"] == 4
        assert s3["eci_band"] == "low"
        assert len(s3["contradictions"]) > 0
        assert len(s3["evidence_items"]) == 2

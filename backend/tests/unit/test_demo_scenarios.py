"""
Unit tests for deterministic demo scenarios.

Validates that demo scenarios run cleanly offline, have complete metadata,
and produce meaningful analyst review checklists with evidence ID citations.
"""

import pytest

from evaluation.demo_scenarios import get_demo_scenarios


class TestDemoScenarios:
    """Tests for demonstration scenarios execution."""

    def test_all_three_demos_execute(self):
        """All 3 demo scenarios must execute cleanly and return complete results."""
        demos = get_demo_scenarios()
        assert len(demos) == 3

        names = [d.scenario_name for d in demos]
        assert "demo_strong" in names
        assert "demo_zero" in names
        assert "demo_contradicted" in names

    def test_demo_strong_characteristics(self):
        """Demo Strong must have citations and positive ECI factors."""
        demos = {d.scenario_name: d for d in get_demo_scenarios()}
        d1 = demos["demo_strong"]

        assert d1.evidence_count > 0
        assert d1.eci_score > 50
        assert len(d1.dossier.evidence_citations) > 0
        assert len(d1.analyst_checklist) > 0

    def test_demo_zero_characteristics(self):
        """Demo Zero must reflect zero evidence state."""
        demos = {d.scenario_name: d for d in get_demo_scenarios()}
        d2 = demos["demo_zero"]

        assert d2.evidence_count == 0
        assert d2.eci_score == 0
        assert d2.eci_band == "low"
        assert len(d2.dossier.evidence_citations) == 0

    def test_demo_contradicted_characteristics(self):
        """Demo Contradicted must flag contradictions and prompt analyst discrepancy review."""
        demos = {d.scenario_name: d for d in get_demo_scenarios()}
        d3 = demos["demo_contradicted"]

        assert len(d3.contradictions) > 0
        # Checklist must reference evidence ID / discrepancy
        checklist_text = " ".join(d3.analyst_checklist)
        assert "[E1]" in checklist_text or "discrepancy" in checklist_text.lower()

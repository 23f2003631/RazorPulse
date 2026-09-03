"""
RazorPulse Deterministic Demo Runner.

Executes 3 representative demonstration scenarios without external API calls
or network access. Illustrates how RazorPulse corroborates legitimate commercial surges,
gracefully handles zero-evidence anomalies, and detects conflicting claims.

USAGE:
  cd backend
  python scripts/run_demo.py
"""

import sys
from pathlib import Path

# Add backend directory to sys.path
_BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BACKEND_DIR))

from evaluation.demo_scenarios import get_demo_scenarios


def main():
    print("=" * 76)
    print("RAZORPULSE -- DETERMINISTIC INVESTIGATION DEMO")
    print("=" * 76)
    print("Running 3 representative offline demonstration scenarios...")
    print("Note: Demonstrates pure deterministic scoring and dossier synthesis.")
    print("=" * 76)

    demos = get_demo_scenarios()

    for idx, demo in enumerate(demos, start=1):
        print(f"\n[{idx}/3] {demo.scenario_title.upper()}")
        print("-" * 76)
        print(f"Merchant:             {demo.merchant_name}")
        print(f"Observed Anomaly:     {demo.anomaly_summary}")
        print(f"Semantic Expectation: {demo.semantic_expectation}")
        print(f"Discovered Evidence:  {demo.evidence_count} item(s)")
        print(f"Calculated ECI Score: {demo.eci_score}/100 ({demo.eci_band.upper()})")

        print("\nItemized ECI Factors:")
        for factor in demo.factors_summary:
            pts = f"{factor['points']:+.0f}"
            print(f"  * {factor['category']:<28} {pts:>5} pts | {factor['explanation']}")

        if demo.contradictions:
            print("\nFlagged Contradictions:")
            for contra in demo.contradictions:
                print(f"  [!] {contra}")

        print("\nAnalyst Review Guidance (Checklist):")
        for check in demo.analyst_checklist[:3]:
            print(f"  [ ] {check}")

        print("-" * 76)

    print("\n" + "=" * 76)
    print("DEMO COMPLETE -- All 3 scenarios evaluated successfully.")
    print("=" * 76)


if __name__ == "__main__":
    main()

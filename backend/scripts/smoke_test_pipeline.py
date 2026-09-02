"""
Live Investigation Pipeline Smoke Test.

Executes the complete RazorPulse investigation pipeline end-to-end
using live configured Exa AI and Google Gemini API keys against a synthetic
risk event.

USAGE:
    cd backend
    python scripts/smoke_test_pipeline.py

REQUIREMENTS:
    - Valid EXA_API_KEY and GEMINI_API_KEY in .env
"""

from datetime import datetime, timezone
import os
import sys

# Add backend directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()


def main():
    print("=" * 70)
    print("RazorPulse — Live Investigation Pipeline Smoke Test")
    print("=" * 70)

    from app.config.settings import get_settings
    settings = get_settings()

    # 1. Verify credentials
    if not settings.has_exa_credentials():
        print("\n❌ EXA_API_KEY is not configured or is a placeholder in .env")
        sys.exit(1)
    if not settings.has_gemini_credentials():
        print("\n❌ GEMINI_API_KEY is not configured or is a placeholder in .env")
        sys.exit(1)

    print("\n✓ Credentials verified:")
    print(f"  - Exa key prefix: {settings.EXA_API_KEY[:8]}...")
    print(f"  - Gemini key prefix: {settings.GEMINI_API_KEY[:8]}...")
    print(f"  - Gemini Model: {settings.GEMINI_MODEL}")

    # 2. Setup synthetic test risk event
    test_merchant_name = "Zomato"
    test_merchant_domain = "zomato.com"
    test_anomaly_type = "transaction_velocity_spike"
    test_occurred_at = datetime.now(timezone.utc)

    print(f"\nTarget Synthetic Anomaly:")
    print(f"  - Merchant: {test_merchant_name} ({test_merchant_domain})")
    print(f"  - Anomaly Type: {test_anomaly_type}")
    print(f"  - Timestamp: {test_occurred_at.isoformat()}")

    # 3. Step A: Exa Discovery
    print("\n[Step 1/4] Running Exa External Evidence Search...")
    from app.services.exa.search_strategy import ExaSearchStrategy
    search_strategy = ExaSearchStrategy()

    evidence_items, queries = search_strategy.execute_search(
        merchant_name=test_merchant_name,
        merchant_domain=test_merchant_domain,
        occurred_at=test_occurred_at,
        anomaly_type=test_anomaly_type,
        num_results_per_query=3,
        max_queries=3,
    )

    print(f"✓ Executed {len(queries)} search query intents")
    for q in queries:
        print(f"  - [{q['intent']}]: {q['query_text']} (found {q['results_count']} results)")
    print(f"✓ Discovered and deduplicated {len(evidence_items)} total evidence items")

    if not evidence_items:
        print("\n⚠️ No live evidence items found. Proceeding to zero-evidence test...")

    # 4. Step B: Gemini Verification
    print("\n[Step 2/4] Running Gemini Structured Verification...")
    from app.services.gemini.verifier import GeminiVerifier
    from uuid import uuid4
    verifier = GeminiVerifier()
    test_inv_id = uuid4()

    verification_result = verifier.verify_all_evidence(
        investigation_id=test_inv_id,
        evidence_items=evidence_items,
        merchant_name=test_merchant_name,
        merchant_domain=test_merchant_domain,
        occurred_at=test_occurred_at,
        anomaly_type=test_anomaly_type,
        risk_reason="Testing live pipeline execution with public merchant context",
    )

    print(f"✓ Verified {len(verification_result.items)} evidence items")
    for item in verification_result.items[:3]:
        print(f"  - Item {str(item.evidence_id)[:8]}:")
        print(f"      Entity Match: {item.merchant_match.value}")
        print(f"      Temporal Match: {item.temporal_match.value}")
        print(f"      Support Level: {item.explanation_support.value}")
        print(f"      Credibility: {item.source_credibility.value}")
        print(f"      Summary: {item.reasoning_summary[:80]}...")

    # 5. Step C: Deterministic ECI Scoring
    print("\n[Step 3/4] Running Deterministic ECI Scoring Engine (v1)...")
    from app.services.scoring.eci_engine import ECIEngine
    eci_result = ECIEngine.calculate_eci(
        verification_result=verification_result,
        evidence_items=evidence_items,
    )

    print(f"\n=======================================================")
    print(f"  EVENT CORROBORATION INDEX: {eci_result.eci_score}/100")
    print(f"  Band: {eci_result.band_label}")
    print(f"  Confidence: {eci_result.confidence_level}")
    print(f"  Positive Points: +{eci_result.positive_points}")
    print(f"  Penalty Points: -{eci_result.penalty_points}")
    print(f"=======================================================")
    print("\nItemized Factor Breakdown:")
    for f in eci_result.factors:
        sign = "+" if f.points_awarded >= 0 else ""
        print(f"  {sign}{f.points_awarded:>4} pts | {f.name:<35} | {f.explanation}")

    # 6. Step D: Dossier Synthesis
    print("\n[Step 4/4] Generating Evidence Dossier...")
    from app.services.investigation.dossier_generator import DossierGenerator
    synthetic_event_dict = {
        "id": str(uuid4()),
        "merchant_name": test_merchant_name,
        "merchant_domain": test_merchant_domain,
        "anomaly_type": test_anomaly_type,
        "occurred_at": test_occurred_at,
        "baseline_transaction_count": 100,
        "observed_transaction_count": 800,
        "percentage_change": 700.0,
        "currency": "INR",
        "risk_reason": "Simulated live smoke test event",
    }

    dossier = DossierGenerator.generate_dossier(
        investigation_id=test_inv_id,
        risk_event=synthetic_event_dict,
        evidence_items=evidence_items,
        verification_result=verification_result,
        eci_result=eci_result,
        executed_queries=queries,
    )

    print("\n✓ Dossier Generated Successfully:")
    print(f"  - Executive Summary:\n    {dossier.executive_summary}\n")
    print(f"  - Evidence Citations: {len(dossier.evidence_citations)}")
    for c in dossier.evidence_citations[:3]:
        print(f"    {c.citation_id} {c.title or 'Untitled'} ({c.source_domain}) - {c.key_fact[:60]}...")
    print(f"\n  - Analyst Review Checklist:")
    for idx, item in enumerate(dossier.analyst_review_checklist, start=1):
        print(f"    {idx}. {item}")

    print("\n" + "=" * 70)
    print("✓ ALL PIPELINE SMOKE TESTS COMPLETED SUCCESSFULLY")
    print("=" * 70)


if __name__ == "__main__":
    main()

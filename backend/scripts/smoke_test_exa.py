"""
Exa AI Connectivity Smoke Test.

This script verifies that the Exa API key is valid and the service
is reachable. It performs a real API call — run only when you have
a valid EXA_API_KEY in your .env file.

USAGE:
    cd backend
    python scripts/smoke_test_exa.py

REQUIREMENTS:
    - Valid EXA_API_KEY in .env
    - Dependencies installed (pip install -r requirements.txt)
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def main():
    print("=" * 60)
    print("RazorPulse — Exa AI Connectivity Smoke Test")
    print("=" * 60)

    from app.config.settings import get_settings
    settings = get_settings()

    if not settings.has_exa_credentials():
        print("\n❌ EXA_API_KEY is not configured or is a placeholder.")
        print("   Set a valid EXA_API_KEY in your .env file.")
        sys.exit(1)

    print("\n✓ EXA_API_KEY is configured")
    print(f"  Key prefix: {settings.EXA_API_KEY[:8]}...")

    print("\nInitializing Exa client...")
    try:
        from app.services.exa.client import ExaClient
        client = ExaClient()
        print("✓ Exa client initialized")
    except Exception as e:
        print(f"\n❌ Failed to initialize Exa client: {e}")
        sys.exit(1)

    print("\nRunning health check (minimal search)...")
    result = client.health_check()
    if result["status"] == "ok":
        print(f"✓ Exa health check passed (result_count={result['result_count']})")
    else:
        print(f"❌ Exa health check failed: {result.get('error', 'Unknown error')}")
        sys.exit(1)

    print("\nRunning merchant event search test...")
    try:
        response = client.search_merchant_events(
            merchant_name="Zomato",
            merchant_domain="zomato.com",
            num_results=3,
        )
        print(f"✓ Search returned {len(response.results)} results")
        for i, r in enumerate(response.results):
            print(f"  [{i+1}] {r.title or 'No title'}")
            print(f"      URL: {r.url}")
            print(f"      Score: {r.score}")
    except Exception as e:
        print(f"❌ Merchant event search failed: {e}")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("✓ ALL EXA SMOKE TESTS PASSED")
    print("=" * 60)


if __name__ == "__main__":
    main()

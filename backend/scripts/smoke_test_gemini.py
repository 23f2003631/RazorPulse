"""
Google Gemini Connectivity Smoke Test.

This script verifies that the Gemini API key is valid and the service
is reachable. It performs a real API call — run only when you have
a valid GEMINI_API_KEY in your .env file.

USAGE:
    cd backend
    python scripts/smoke_test_gemini.py

REQUIREMENTS:
    - Valid GEMINI_API_KEY in .env
    - Dependencies installed (pip install -r requirements.txt)
"""

import sys
import os

# Add backend to path and resolve env paths
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT_DIR = os.path.dirname(BACKEND_DIR)
sys.path.insert(0, BACKEND_DIR)

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from dotenv import load_dotenv

# Load environment variables: root .env first, then backend/.env overrides it
root_env = os.path.join(ROOT_DIR, ".env")
backend_env = os.path.join(BACKEND_DIR, ".env")
if os.path.exists(root_env):
    load_dotenv(dotenv_path=root_env)
if os.path.exists(backend_env):
    load_dotenv(dotenv_path=backend_env, override=True)


def main():
    print("=" * 60)
    print("RazorPulse — Google Gemini Connectivity Smoke Test")
    print("=" * 60)

    from app.config.settings import get_settings
    settings = get_settings()

    if not settings.has_gemini_credentials():
        print("\n❌ GEMINI_API_KEY is not configured or is a placeholder.")
        print("   Set a valid GEMINI_API_KEY in your .env file.")
        sys.exit(1)

    print("\n✓ GEMINI_API_KEY is configured")
    print(f"  Key prefix: {settings.GEMINI_API_KEY[:8]}...")
    print(f"  Model: {settings.GEMINI_MODEL}")

    print("\nInitializing Gemini client...")
    try:
        from app.services.gemini.client import GeminiClient
        client = GeminiClient()
        print("✓ Gemini client initialized")
    except Exception as e:
        print(f"\n❌ Failed to initialize Gemini client: {e}")
        sys.exit(1)

    print("\nRunning health check (basic prompt)...")
    result = client.health_check()
    if result["status"] == "ok":
        print(f"✓ Gemini health check passed")
        print(f"  Model: {result['model']}")
        print(f"  Response: {result['response_preview']}")
    else:
        print(f"❌ Gemini health check failed: {result.get('error', 'Unknown error')}")
        sys.exit(1)

    print("\nRunning structured output test...")
    result = client.test_structured_output()
    if result["status"] == "ok":
        print(f"✓ Structured output test passed")
        print(f"  Model: {result['model']}")
        print(f"  Parsed response: {result['parsed_response']}")
    else:
        print(f"❌ Structured output test failed: {result.get('error', 'Unknown error')}")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("✓ ALL GEMINI SMOKE TESTS PASSED")
    print("=" * 60)


if __name__ == "__main__":
    main()

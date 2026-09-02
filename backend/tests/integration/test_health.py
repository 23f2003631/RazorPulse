"""
Integration tests for the health endpoint.

Uses FastAPI's TestClient to verify the health check endpoint
works correctly end-to-end.
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestHealthEndpoint:
    """Test suite for GET /health."""

    def test_health_returns_ok(self):
        """Health endpoint should return status ok."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    def test_health_returns_app_name(self):
        """Health response should include app name."""
        response = client.get("/health")
        data = response.json()
        assert data["app"] == "RazorPulse"

    def test_health_returns_version(self):
        """Health response should include version."""
        response = client.get("/health")
        data = response.json()
        assert "version" in data
        assert data["version"] == "0.1.0"

    def test_health_returns_environment(self):
        """Health response should include environment."""
        response = client.get("/health")
        data = response.json()
        assert "environment" in data

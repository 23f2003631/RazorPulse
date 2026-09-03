"""
Unit tests for Pipeline Reproducibility Metadata schema.

Validates:
- Schema instantiation and defaults
- Required operational metadata fields (pipeline_version, eci_version, gemini_model, prompt_version)
- Stage duration recording
- Evidence and query counts tracking
- Serialization into dict/JSON for Supabase persistence
"""

from datetime import datetime, timezone
import pytest

from app.schemas.pipeline_metadata import PipelineMetadata


class TestPipelineMetadata:
    """Tests for reproducibility and operational metadata schema."""

    def test_pipeline_metadata_instantiation_and_defaults(self):
        """Should initialize with expected defaults for versions and timestamps."""
        meta = PipelineMetadata(
            gemini_model="gemini-3.5-flash-lite",
            query_count=3,
            evidence_discovered_count=5,
            evidence_usable_count=5,
            evidence_verified_count=3,
            evidence_skipped_count=2,
            evidence_failed_count=0,
            stage_durations={
                "searching": 1.25,
                "verifying": 2.10,
                "scoring": 0.01,
                "dossier": 0.02,
                "persistence": 0.15,
            },
            total_duration_seconds=3.53,
        )

        assert meta.pipeline_version == "0.3.0"
        assert meta.eci_version == "v1"
        assert meta.search_strategy_version == "v1"
        assert meta.verification_prompt_version == "v1"
        assert meta.gemini_model == "gemini-3.5-flash-lite"
        assert meta.total_duration_seconds == 3.53
        assert meta.stage_durations["searching"] == 1.25
        assert meta.evidence_verified_count == 3
        assert meta.evidence_skipped_count == 2

    def test_pipeline_metadata_json_serialization(self):
        """Should serialize cleanly to JSON for Supabase JSONB column persistence."""
        meta = PipelineMetadata(
            gemini_model="gemini-3.5-flash-lite",
            stage_durations={"searching": 0.5, "scoring": 0.02},
        )
        data = meta.model_dump(mode="json")
        assert isinstance(data, dict)
        assert data["pipeline_version"] == "0.3.0"
        assert data["verification_prompt_version"] == "v1"
        assert "started_at" in data
        assert data["stage_durations"]["searching"] == 0.5

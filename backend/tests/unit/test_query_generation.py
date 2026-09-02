"""
Unit tests for Exa Query Intent Builder.
"""

from datetime import datetime, timezone
import pytest

from app.services.exa.query_builder import QueryIntent, QueryIntentBuilder


class TestQueryIntentBuilder:
    """Test suite for QueryIntentBuilder."""

    def test_build_queries_full_context(self):
        """Should generate structured queries across multiple intents when full context is present."""
        occurred_at = datetime(2026, 8, 28, 14, 30, tzinfo=timezone.utc)
        queries = QueryIntentBuilder.build_queries(
            merchant_name="UrbanCraft India",
            merchant_domain="urbancraft.in",
            occurred_at=occurred_at,
            anomaly_type="transaction_velocity_spike",
            max_queries=4,
        )

        assert len(queries) <= 4
        assert len(queries) >= 3

        intents = [q.intent for q in queries]
        assert QueryIntent.TIMEFRAME_EVENT in intents
        assert QueryIntent.MERCHANT_ANNOUNCEMENT in intents
        assert QueryIntent.COMMERCIAL_CAMPAIGN in intents

        # Check timeframe query mentions August 2026
        tf_query = next(q for q in queries if q.intent == QueryIntent.TIMEFRAME_EVENT)
        assert "August 2026" in tf_query.query_text
        assert "UrbanCraft India" in tf_query.query_text
        assert tf_query.date_filter is not None

        # Check domain site query
        ann_query = next(q for q in queries if q.intent == QueryIntent.MERCHANT_ANNOUNCEMENT)
        assert "site:urbancraft.in" in ann_query.query_text

    def test_build_queries_missing_domain(self):
        """Should build queries safely without domain search intent if domain is missing."""
        occurred_at = datetime(2026, 8, 28, 14, 30, tzinfo=timezone.utc)
        queries = QueryIntentBuilder.build_queries(
            merchant_name="QuickDeal Bazaar",
            merchant_domain=None,
            occurred_at=occurred_at,
            anomaly_type="volume_surge",
        )

        intents = [q.intent for q in queries]
        assert QueryIntent.MERCHANT_ANNOUNCEMENT not in intents
        assert QueryIntent.TIMEFRAME_EVENT in intents
        assert QueryIntent.COMMERCIAL_CAMPAIGN in intents

    def test_build_queries_missing_date(self):
        """Should fallback to identity context search if anomaly date is not provided."""
        queries = QueryIntentBuilder.build_queries(
            merchant_name="QuickDeal Bazaar",
            merchant_domain=None,
            occurred_at=None,
        )

        intents = [q.intent for q in queries]
        assert QueryIntent.TIMEFRAME_EVENT not in intents
        assert QueryIntent.IDENTITY_CONTEXT in intents

    def test_build_queries_max_bounding(self):
        """Max queries parameter should strictly bound returned query count."""
        occurred_at = datetime(2026, 8, 28, 14, 30, tzinfo=timezone.utc)
        queries = QueryIntentBuilder.build_queries(
            merchant_name="Test Merchant",
            merchant_domain="test.com",
            occurred_at=occurred_at,
            anomaly_type="transaction_velocity_spike",
            max_queries=2,
        )
        assert len(queries) == 2

    def test_build_queries_deduplication(self):
        """Should not generate duplicate query texts."""
        queries = QueryIntentBuilder.build_queries(
            merchant_name="Test Merchant",
            merchant_domain="test.com",
            occurred_at=datetime(2026, 8, 28, tzinfo=timezone.utc),
        )
        query_texts = [q.query_text for q in queries]
        assert len(query_texts) == len(set(query_texts))

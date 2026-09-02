"""
Unit tests for Evidence Normalization and URL Deduplication.
"""

from uuid import uuid4
import pytest

from app.schemas.evidence import NormalizedEvidence, SourceType, canonicalize_url
from app.services.exa.client import ExaSearchResult
from app.services.exa.normalizer import (
    classify_source_type,
    deduplicate_evidence,
    extract_domain,
    normalize_exa_result,
)


class TestEvidenceNormalization:
    """Test suite for evidence normalizer functions."""

    def test_canonicalize_url_tracking_parameters(self):
        """Should strip tracking parameters (utm_*, fbclid, etc.) while preserving real paths."""
        raw_url = "https://WWW.YourStory.com/2026/08/article/?utm_source=twitter&utm_medium=social&fbclid=12345&id=99#frag"
        canon = canonicalize_url(raw_url)
        assert "utm_source" not in canon
        assert "fbclid" not in canon
        assert "id=99" in canon
        assert canon.startswith("https://yourstory.com/2026/08/article")

    def test_canonicalize_url_trailing_slash(self):
        """Should normalize trailing slashes."""
        url1 = "https://example.com/news/"
        url2 = "https://example.com/news"
        assert canonicalize_url(url1) == canonicalize_url(url2)

    def test_extract_domain(self):
        """Should cleanly extract lowercase netloc without www."""
        assert extract_domain("https://www.economictimes.indiatimes.com/article") == "economictimes.indiatimes.com"
        assert extract_domain("http://urbancraft.in/page") == "urbancraft.in"
        assert extract_domain("") == "unknown"

    def test_classify_source_type(self):
        """Should categorize domains into correct structural metadata types."""
        # Merchant official
        assert classify_source_type("https://urbancraft.in/sale", "urbancraft.in") == SourceType.MERCHANT_OFFICIAL
        assert classify_source_type("https://blog.urbancraft.in/post", "urbancraft.in") == SourceType.MERCHANT_OFFICIAL

        # News media
        assert classify_source_type("https://yourstory.com/story", "urbancraft.in") == SourceType.NEWS_MEDIA
        assert classify_source_type("https://economictimes.indiatimes.com/news", "urbancraft.in") == SourceType.NEWS_MEDIA

        # Press release
        assert classify_source_type("https://www.prnewswire.com/news-releases/123", "urbancraft.in") == SourceType.PRESS_RELEASE

        # Social
        assert classify_source_type("https://twitter.com/brand/status/123", "urbancraft.in") == SourceType.SOCIAL_COMMUNITY

        # General web
        assert classify_source_type("https://random-personal-blog.xyz/post", "urbancraft.in") == SourceType.GENERAL_WEB

    def test_normalize_exa_result(self):
        """Should normalize ExaSearchResult to NormalizedEvidence with stable UUID."""
        raw = ExaSearchResult(
            title="Brand Launch Event",
            url="https://yourstory.com/2026/08/brand-launch",
            published_date="2026-08-28T10:00:00Z",
            author="Tech Desk",
            score=0.91,
            text="Text snippet about the launch.",
            highlights=["launch event", "huge discount"],
        )
        query_id = uuid4()
        norm = normalize_exa_result(
            result=raw,
            query_id=query_id,
            query_text='"Brand" launch',
            query_intent="commercial_campaign",
            merchant_domain="brand.com",
        )

        assert norm.evidence_id is not None
        assert norm.url == "https://yourstory.com/2026/08/brand-launch"
        assert norm.source_domain == "yourstory.com"
        assert norm.source_type == SourceType.NEWS_MEDIA
        assert norm.external_score == 0.91
        assert norm.highlights == ["launch event", "huge discount"]

    def test_deduplicate_evidence(self):
        """Should deduplicate evidence items by canonical URL, merging highlights and retaining highest score."""
        ev1 = NormalizedEvidence(
            evidence_id=uuid4(),
            url="https://yourstory.com/article?utm_source=tw",
            title="Article A",
            source_domain="yourstory.com",
            source_type=SourceType.NEWS_MEDIA,
            content_snippet="Short snippet.",
            highlights=["H1"],
            discovery_query="query 1",
            discovery_query_intent="intent_1",
            external_score=0.75,
        )
        ev2 = NormalizedEvidence(
            evidence_id=uuid4(),
            url="https://yourstory.com/article",
            title="Article A",
            source_domain="yourstory.com",
            source_type=SourceType.NEWS_MEDIA,
            content_snippet="A much longer and more comprehensive snippet with full details.",
            highlights=["H2", "H1"],
            discovery_query="query 2",
            discovery_query_intent="intent_2",
            external_score=0.88,
        )
        ev3 = NormalizedEvidence(
            evidence_id=uuid4(),
            url="https://economictimes.indiatimes.com/other",
            title="Article B",
            source_domain="economictimes.indiatimes.com",
            source_type=SourceType.NEWS_MEDIA,
            content_snippet="Different article.",
            highlights=[],
            discovery_query="query 3",
            discovery_query_intent="intent_3",
            external_score=0.90,
        )

        deduped = deduplicate_evidence([ev1, ev2, ev3])
        assert len(deduped) == 2

        # Verify merged item has both highlights and longer snippet and higher score
        merged_item = next(item for item in deduped if "yourstory.com" in item.url)
        assert set(merged_item.highlights) == {"H1", "H2"}
        assert len(merged_item.content_snippet) > len("Short snippet.")
        assert merged_item.external_score == 0.88

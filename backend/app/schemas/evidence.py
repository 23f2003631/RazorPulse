"""
Evidence schemas and normalization models.

Represents external evidence discovered by Exa or other external sources.
Maintains full provenance (query_id, retrieved_at, source_domain, raw score).
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class SourceType(str, Enum):
    """
    Metadata classification of the source domain.

    NOTE: source_type is purely a domain categorization (metadata),
    NOT a measure of factual credibility. Credibility is evaluated
    separately during verification.
    """

    MERCHANT_OFFICIAL = "merchant_official"  # Official merchant site/domain
    NEWS_MEDIA = "news_media"                # Established news publication
    PRESS_RELEASE = "press_release"          # PR distribution network
    SOCIAL_COMMUNITY = "social_community"    # Social platform, forum, reddit
    INDUSTRY_PORTAL = "industry_portal"      # Trade journal, tech blog, directory
    GENERAL_WEB = "general_web"              # Other public web page


class NormalizedEvidence(BaseModel):
    """
    Normalized internal representation of an external evidence item.

    Decouples RazorPulse from Exa's raw API response format and assigns
    a stable evidence_id for pipeline-wide traceability.
    """

    evidence_id: UUID = Field(
        default_factory=uuid4,
        description="Unique identifier for this evidence item throughout the pipeline",
    )
    url: str = Field(..., description="Canonical or raw URL of the discovered evidence")
    title: Optional[str] = Field(default=None, description="Title of the web page or article")
    source_domain: str = Field(..., description="Extracted domain (e.g. yourstory.com)")
    source_type: SourceType = Field(
        default=SourceType.GENERAL_WEB,
        description="Domain classification (metadata only; not credibility)",
    )
    published_at: Optional[str] = Field(
        default=None,
        description="Publication date string if available from source metadata",
    )
    retrieved_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when evidence was retrieved",
    )
    content_snippet: Optional[str] = Field(
        default=None,
        description="Text content snippet or summary extracted from source",
    )
    highlights: list[str] = Field(
        default_factory=list,
        description="Key extracted highlight snippets",
    )
    discovery_query: str = Field(
        ...,
        description="Search query string that discovered this evidence",
    )
    discovery_query_intent: str = Field(
        ...,
        description="Structured query intent category that produced this evidence",
    )
    external_score: Optional[float] = Field(
        default=None,
        description="Raw search relevance score from the search provider",
    )


def canonicalize_url(raw_url: str) -> str:
    """
    Conservative URL normalization for deduplication.

    Normalizes scheme (lowercase), netloc (lowercase, strips 'www.'),
    strips trailing slashes, and removes common tracking parameters
    (utm_*, fbclid, gclid, ref) without altering meaningful query keys.
    """
    if not raw_url:
        return ""
    try:
        parsed = urlparse(raw_url.strip())
        scheme = parsed.scheme.lower() or "https"
        netloc = parsed.netloc.lower()
        if netloc.startswith("www."):
            netloc = netloc[4:]

        path = parsed.path.rstrip("/")
        if not path:
            path = "/"

        # Filter tracking parameters
        tracking_prefixes = ("utm_", "fbclid", "gclid", "_ga", "ref_")
        query_params = parse_qs(parsed.query, keep_blank_values=False)
        cleaned_params = {
            k: v for k, v in query_params.items()
            if not any(k.lower().startswith(prefix) for prefix in tracking_prefixes)
        }
        cleaned_query = urlencode(cleaned_params, doseq=True)

        return urlunparse((scheme, netloc, path, parsed.params, cleaned_query, ""))
    except Exception:
        return raw_url.strip()

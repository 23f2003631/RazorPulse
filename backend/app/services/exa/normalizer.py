"""
Evidence Normalization and Deduplication Service.

Transforms raw search results into canonical NormalizedEvidence items,
classifies source domain metadata, and performs conservative deduplication.
"""

from typing import Optional
from urllib.parse import urlparse
from uuid import UUID

from app.schemas.evidence import NormalizedEvidence, SourceType, canonicalize_url
from app.services.exa.client import ExaSearchResult

# Recognized domain classifications (for metadata classification only; not credibility)
KNOWN_NEWS_DOMAINS = {
    "economictimes.indiatimes.com", "yourstory.com", "livemint.com", "business-standard.com",
    "ndtv.com", "thehindu.com", "indianexpress.com", "hindustantimes.com", "reuters.com",
    "bloomberg.com", "techcrunch.com", "inc42.com", "moneycontrol.com", "forbes.com",
    "cnbctv18.com", "timesofindia.indiatimes.com", "financialexpress.com",
}

KNOWN_PRESS_DOMAINS = {
    "prnewswire.com", "businesswire.com", "globenewswire.com", "pib.gov.in", "pressreleasepoint.com"
}

KNOWN_SOCIAL_DOMAINS = {
    "reddit.com", "twitter.com", "x.com", "instagram.com", "youtube.com",
    "linkedin.com", "facebook.com", "threads.net"
}

KNOWN_INDUSTRY_DOMAINS = {
    "techcircle.in", "medianama.com", "entrackr.com", "vccircle.com", "pitchbook.com",
    "producthunt.com", "g2.com", "capterra.com", "crunchbase.com"
}


def extract_domain(url: str) -> str:
    """Extract clean lowercase domain from URL or domain string."""
    if not url:
        return "unknown"
    try:
        url_to_parse = url.strip()
        if not (url_to_parse.startswith("http://") or url_to_parse.startswith("https://") or url_to_parse.startswith("//")):
            url_to_parse = "https://" + url_to_parse
        netloc = urlparse(url_to_parse).netloc.lower()
        if netloc.startswith("www."):
            netloc = netloc[4:]
        return netloc or "unknown"
    except Exception:
        return "unknown"


def classify_source_type(url: str, merchant_domain: Optional[str] = None) -> SourceType:
    """
    Classify the source type based on domain structure.

    NOTE: This is purely a structural metadata categorization.
    It does NOT determine factual credibility.
    """
    domain = extract_domain(url)

    if merchant_domain:
        clean_merchant_domain = extract_domain(merchant_domain)
        if clean_merchant_domain and (domain == clean_merchant_domain or domain.endswith("." + clean_merchant_domain)):
            return SourceType.MERCHANT_OFFICIAL

    if domain in KNOWN_NEWS_DOMAINS or any(domain.endswith("." + d) for d in KNOWN_NEWS_DOMAINS):
        return SourceType.NEWS_MEDIA

    if domain in KNOWN_PRESS_DOMAINS or any(domain.endswith("." + d) for d in KNOWN_PRESS_DOMAINS):
        return SourceType.PRESS_RELEASE

    if domain in KNOWN_SOCIAL_DOMAINS or any(domain.endswith("." + d) for d in KNOWN_SOCIAL_DOMAINS):
        return SourceType.SOCIAL_COMMUNITY

    if domain in KNOWN_INDUSTRY_DOMAINS or any(domain.endswith("." + d) for d in KNOWN_INDUSTRY_DOMAINS):
        return SourceType.INDUSTRY_PORTAL

    return SourceType.GENERAL_WEB


def normalize_exa_result(
    result: ExaSearchResult,
    query_id: UUID,
    query_text: str,
    query_intent: str,
    merchant_domain: Optional[str] = None,
) -> NormalizedEvidence:
    """
    Normalize a single Exa search result into a NormalizedEvidence schema.
    """
    canonical_url = canonicalize_url(result.url)
    domain = extract_domain(canonical_url or result.url)
    source_type = classify_source_type(canonical_url or result.url, merchant_domain)

    return NormalizedEvidence(
        url=canonical_url or result.url,
        title=result.title,
        source_domain=domain,
        source_type=source_type,
        published_at=result.published_date,
        content_snippet=result.text,
        highlights=result.highlights or [],
        discovery_query=query_text,
        discovery_query_intent=query_intent,
        external_score=result.score,
    )


def deduplicate_evidence(evidence_list: list[NormalizedEvidence]) -> list[NormalizedEvidence]:
    """
    Deduplicate evidence items based on canonical URL.

    If multiple queries return the same canonical URL, merges highlights,
    preserves the richer snippet, and retains the higher external score.
    """
    unique_by_url: dict[str, NormalizedEvidence] = {}

    for item in evidence_list:
        canon_url = canonicalize_url(item.url)
        if canon_url not in unique_by_url:
            unique_by_url[canon_url] = item
        else:
            existing = unique_by_url[canon_url]
            # Merge highlights
            combined_highlights = list(dict.fromkeys(existing.highlights + item.highlights))
            existing.highlights = combined_highlights

            # Keep the longer snippet if available
            if item.content_snippet and (not existing.content_snippet or len(item.content_snippet) > len(existing.content_snippet)):
                existing.content_snippet = item.content_snippet

            # Keep the higher score
            if item.external_score is not None:
                if existing.external_score is None or item.external_score > existing.external_score:
                    existing.external_score = item.external_score

    return list(unique_by_url.values())

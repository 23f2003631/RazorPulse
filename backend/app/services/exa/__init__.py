# Exa AI — External event discovery service
from app.services.exa.client import ExaClient, ExaSearchResponse, ExaSearchResult
from app.services.exa.normalizer import (
    classify_source_type,
    deduplicate_evidence,
    extract_domain,
    normalize_exa_result,
)
from app.services.exa.query_builder import QueryIntent, QueryIntentBuilder, StructuredSearchQuery
from app.services.exa.search_strategy import ExaSearchStrategy

__all__ = [
    "ExaClient",
    "ExaSearchResult",
    "ExaSearchResponse",
    "QueryIntent",
    "QueryIntentBuilder",
    "StructuredSearchQuery",
    "ExaSearchStrategy",
    "classify_source_type",
    "extract_domain",
    "normalize_exa_result",
    "deduplicate_evidence",
]

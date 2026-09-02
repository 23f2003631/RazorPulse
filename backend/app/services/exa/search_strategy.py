"""
Exa Search Strategy Service.

Coordinates multi-intent query generation, search execution,
evidence normalization, and deduplication for an investigation.
"""

from datetime import datetime
from typing import Optional

from app.core.exceptions import ExaServiceError
from app.core.logging import get_logger
from app.schemas.evidence import NormalizedEvidence
from app.services.exa.client import ExaClient
from app.services.exa.normalizer import deduplicate_evidence, normalize_exa_result
from app.services.exa.query_builder import QueryIntentBuilder, StructuredSearchQuery

logger = get_logger("exa_search_strategy")


class ExaSearchStrategy:
    """
    Orchestrates external evidence discovery using Exa AI.
    """

    def __init__(self, client: Optional[ExaClient] = None):
        """Initialize with an optional injected client."""
        self._client = client

    def _get_client(self) -> ExaClient:
        if self._client is None:
            self._client = ExaClient()
        return self._client

    def execute_search(
        self,
        merchant_name: str,
        merchant_domain: Optional[str] = None,
        occurred_at: Optional[datetime] = None,
        anomaly_type: Optional[str] = None,
        num_results_per_query: int = 5,
        max_queries: int = 4,
    ) -> tuple[list[NormalizedEvidence], list[dict]]:
        """
        Execute multi-query external evidence discovery for an investigation.

        Args:
            merchant_name: Name of merchant
            merchant_domain: Domain of merchant
            occurred_at: Timestamp of anomaly
            anomaly_type: Anomaly category
            num_results_per_query: Max results per individual query
            max_queries: Max total query intents to execute

        Returns:
            Tuple of (deduplicated NormalizedEvidence items, list of executed query metadata)
        """
        # 1. Build structured query intents
        queries = QueryIntentBuilder.build_queries(
            merchant_name=merchant_name,
            merchant_domain=merchant_domain,
            occurred_at=occurred_at,
            anomaly_type=anomaly_type,
            max_queries=max_queries,
        )

        logger.info(
            "Generated {} query intents for merchant '{}'",
            len(queries),
            merchant_name,
        )

        all_evidence: list[NormalizedEvidence] = []
        executed_queries_meta: list[dict] = []
        client = self._get_client()

        # 2. Execute each search query
        for q in queries:
            try:
                logger.info("Executing Exa query [intent={}]: '{}'", q.intent.value, q.query_text)
                response = client._client.search_and_contents(
                    query=q.query_text,
                    num_results=num_results_per_query,
                    highlights=True,
                    type="auto",
                    start_published_date=q.date_filter,
                )

                query_results_count = len(response.results) if hasattr(response, "results") else 0
                logger.info("Query returned {} results", query_results_count)

                for raw_r in response.results:
                    from app.services.exa.client import ExaSearchResult
                    search_result = ExaSearchResult(
                        title=getattr(raw_r, "title", None),
                        url=raw_r.url,
                        published_date=getattr(raw_r, "published_date", None),
                        author=getattr(raw_r, "author", None),
                        score=getattr(raw_r, "score", None),
                        text=getattr(raw_r, "text", None),
                        highlights=getattr(raw_r, "highlights", None),
                    )
                    norm_item = normalize_exa_result(
                        result=search_result,
                        query_id=q.query_id,
                        query_text=q.query_text,
                        query_intent=q.intent.value,
                        merchant_domain=merchant_domain,
                    )
                    all_evidence.append(norm_item)

                executed_queries_meta.append({
                    "query_id": str(q.query_id),
                    "intent": q.intent.value,
                    "query_text": q.query_text,
                    "results_count": query_results_count,
                    "status": "success",
                })

            except Exception as e:
                logger.warning("Query failed [intent={}]: '{}' - Error: {}", q.intent.value, q.query_text, str(e))
                executed_queries_meta.append({
                    "query_id": str(q.query_id),
                    "intent": q.intent.value,
                    "query_text": q.query_text,
                    "results_count": 0,
                    "status": "failed",
                    "error": str(e),
                })

        # 3. Deduplicate evidence across all executed queries
        deduped = deduplicate_evidence(all_evidence)
        logger.info(
            "Evidence discovery complete: raw={}, deduplicated={}",
            len(all_evidence),
            len(deduped),
        )

        return deduped, executed_queries_meta

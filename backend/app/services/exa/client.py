"""
Exa AI client wrapper.

Exa is used for EXTERNAL EVENT DISCOVERY — finding news articles,
press coverage, and public web evidence that may explain an observed
payment anomaly.

ARCHITECTURAL BOUNDARY:
  Exa DISCOVERS evidence.
  Gemini INTERPRETS/VERIFIES evidence.
  Deterministic rules ENGINE SCORES evidence.
  Human DECIDES.

Exa results are evidence CANDIDATES, not facts.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.config.settings import get_settings
from app.core.exceptions import ConfigurationError, ExaServiceError
from app.core.logging import get_logger

logger = get_logger("exa_client")


@dataclass
class ExaSearchResult:
    """A single search result from Exa."""

    title: Optional[str]
    url: str
    published_date: Optional[str]
    author: Optional[str]
    score: Optional[float]
    text: Optional[str]
    highlights: Optional[list[str]]


@dataclass
class ExaSearchResponse:
    """Response from an Exa search query."""

    results: list[ExaSearchResult]
    query: str
    autoprompt_string: Optional[str] = None


class ExaClient:
    """
    Wrapper around the Exa AI Python SDK.

    Provides methods for searching external events related to
    merchant anomalies.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Exa client.

        Args:
            api_key: Exa API key. If not provided, reads from settings.

        Raises:
            ConfigurationError: If no API key is available.
        """
        settings = get_settings()
        self._api_key = api_key or settings.EXA_API_KEY

        if not self._api_key or self._api_key.startswith("your_"):
            raise ConfigurationError(
                "Exa API key is not configured. Set EXA_API_KEY in .env"
            )

        # Lazy import to avoid import errors when exa-py is not installed
        try:
            from exa_py import Exa
            self._client = Exa(api_key=self._api_key)
        except ImportError:
            raise ConfigurationError("exa-py package is not installed")
        except Exception as e:
            raise ExaServiceError(f"Failed to initialize Exa client: {e}")

        logger.info("Exa client initialized")

    def search_merchant_events(
        self,
        merchant_name: str,
        merchant_domain: Optional[str] = None,
        anomaly_date: Optional[datetime] = None,
        num_results: int = 10,
    ) -> ExaSearchResponse:
        """
        Search for external events related to a merchant.

        Constructs a search query from merchant identity and anomaly context,
        then searches Exa for relevant external evidence.

        Args:
            merchant_name: Name of the merchant.
            merchant_domain: Merchant's web domain (improves relevance).
            anomaly_date: When the anomaly occurred (for temporal filtering).
            num_results: Maximum number of results to return.

        Returns:
            ExaSearchResponse with search results.

        Raises:
            ExaServiceError: If the search fails.
        """
        # Build search query
        query = f"{merchant_name} news"
        if merchant_domain:
            query = f"{merchant_name} site:{merchant_domain} OR {merchant_name} news"

        # Build search parameters
        search_kwargs = {
            "num_results": num_results,
            "type": "auto",
        }

        # Add date filtering if anomaly date is provided
        if anomaly_date:
            # Search for events in a window around the anomaly
            search_kwargs["start_published_date"] = (
                anomaly_date.strftime("%Y-%m-%dT00:00:00.000Z")
            )

        try:
            logger.info(
                "Exa search: query='{}', num_results={}",
                query[:100],
                num_results,
            )

            response = self._client.search_and_contents(
                query=query,
                highlights=True,
                **search_kwargs,
            )

            results = []
            for r in response.results:
                results.append(
                    ExaSearchResult(
                        title=getattr(r, "title", None),
                        url=r.url,
                        published_date=getattr(r, "published_date", None),
                        author=getattr(r, "author", None),
                        score=getattr(r, "score", None),
                        text=getattr(r, "text", None),
                        highlights=getattr(r, "highlights", None),
                    )
                )

            logger.info("Exa search returned {} results", len(results))
            return ExaSearchResponse(
                results=results,
                query=query,
                autoprompt_string=getattr(response, "autoprompt_string", None),
            )

        except Exception as e:
            logger.error("Exa search failed: {}", str(e))
            raise ExaServiceError(f"Search failed: {e}") from e

    def health_check(self) -> dict:
        """
        Verify Exa API connectivity with a minimal test query.

        Returns:
            Dict with connectivity status and result count.
        """
        try:
            response = self._client.search(
                "test connectivity check",
                num_results=1,
            )
            return {
                "status": "ok",
                "service": "exa",
                "result_count": len(response.results),
            }
        except Exception as e:
            logger.error("Exa health check failed: {}", str(e))
            return {
                "status": "error",
                "service": "exa",
                "error": str(e),
            }

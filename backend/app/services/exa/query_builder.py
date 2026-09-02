"""
Exa Query Intent Builder.

Constructs a bounded, deterministic set of structured search query intents
from the risk anomaly context.

ARCHITECTURAL PRINCIPLE:
  Queries represent search HYPOTHESES/INTENTS to discover external context,
  NOT assumed facts. We search to verify if an event occurred.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class QueryIntent(str, Enum):
    """Category of search hypothesis intent."""
    IDENTITY_CONTEXT = "identity_context"            # General merchant background & public profile
    TIMEFRAME_EVENT = "timeframe_event"              # News/events during the anomaly timeframe
    MERCHANT_ANNOUNCEMENT = "merchant_announcement"  # Official domain announcements & press
    COMMERCIAL_CAMPAIGN = "commercial_campaign"      # Sales, campaigns, product launches, viral activity
    ANOMALY_CONTEXT = "anomaly_context"              # Tailored to anomaly type (velocity, geography)


class StructuredSearchQuery(BaseModel):
    """A search query with associated intent and provenance."""
    query_id: UUID = Field(default_factory=uuid4, description="Unique query ID for citation provenance")
    intent: QueryIntent = Field(..., description="Hypothesis category for this search")
    query_text: str = Field(..., description="Actual search string sent to Exa")
    date_filter: Optional[str] = Field(default=None, description="ISO start date filter if applicable")
    domain_filter: Optional[str] = Field(default=None, description="Specific domain filter if applicable")


class QueryIntentBuilder:
    """
    Builds a bounded, deterministic set of queries from risk event context.
    """

    DEFAULT_MAX_QUERIES = 4

    @classmethod
    def build_queries(
        cls,
        merchant_name: str,
        merchant_domain: Optional[str] = None,
        occurred_at: Optional[datetime] = None,
        anomaly_type: Optional[str] = None,
        max_queries: int = DEFAULT_MAX_QUERIES,
    ) -> list[StructuredSearchQuery]:
        """
        Generate structured search queries based on available event context.

        Args:
            merchant_name: Name of merchant
            merchant_domain: Web domain if known
            occurred_at: Timestamp of anomaly
            anomaly_type: Category of anomaly
            max_queries: Maximum number of queries to emit

        Returns:
            List of StructuredSearchQuery instances (max_queries bounded, deduplicated)
        """
        clean_name = merchant_name.strip().strip('"').strip("'")
        queries: list[StructuredSearchQuery] = []
        seen_texts: set[str] = set()

        def add_query(intent: QueryIntent, text: str, date_filter: Optional[str] = None, domain_filter: Optional[str] = None):
            normalized_text = " ".join(text.strip().split())
            if normalized_text and normalized_text not in seen_texts and len(queries) < max_queries:
                seen_texts.add(normalized_text)
                queries.append(
                    StructuredSearchQuery(
                        intent=intent,
                        query_text=normalized_text,
                        date_filter=date_filter,
                        domain_filter=domain_filter,
                    )
                )

        # 1. Timeframe / Event Query (Intent: TIMEFRAME_EVENT)
        # Search for news specifically around the anomaly timeframe
        if occurred_at:
            month_year = occurred_at.strftime("%B %Y")
            iso_start = occurred_at.strftime("%Y-%m-%dT00:00:00.000Z")
            add_query(
                intent=QueryIntent.TIMEFRAME_EVENT,
                text=f'"{clean_name}" news {month_year}',
                date_filter=iso_start,
            )
        else:
            add_query(
                intent=QueryIntent.IDENTITY_CONTEXT,
                text=f'"{clean_name}" company news announcements',
            )

        # 2. Merchant Official Announcement Query (Intent: MERCHANT_ANNOUNCEMENT)
        # Search official site for product launches, flash sales, press releases
        if merchant_domain:
            clean_domain = merchant_domain.lower().replace("http://", "").replace("https://", "").strip("/")
            if clean_domain.startswith("www."):
                clean_domain = clean_domain[4:]
            add_query(
                intent=QueryIntent.MERCHANT_ANNOUNCEMENT,
                text=f"site:{clean_domain} launch OR sale OR announcement OR campaign",
                domain_filter=clean_domain,
            )

        # 3. Commercial / Campaign / Viral Activity Query (Intent: COMMERCIAL_CAMPAIGN)
        # Search public web for commercial catalysts (flash sales, viral posts, influencer features)
        add_query(
            intent=QueryIntent.COMMERCIAL_CAMPAIGN,
            text=f'"{clean_name}" sale OR campaign OR launch OR discount OR viral',
        )

        # 4. Anomaly Context / Surge Explanation Query (Intent: ANOMALY_CONTEXT)
        # Tailor query based on specific anomaly category
        if anomaly_type == "transaction_velocity_spike" or anomaly_type == "volume_surge":
            add_query(
                intent=QueryIntent.ANOMALY_CONTEXT,
                text=f'"{clean_name}" surge OR demand OR sold out OR trending',
            )
        elif anomaly_type == "new_geography":
            add_query(
                intent=QueryIntent.ANOMALY_CONTEXT,
                text=f'"{clean_name}" expansion OR market launch OR international',
            )
        else:
            add_query(
                intent=QueryIntent.IDENTITY_CONTEXT,
                text=f'"{clean_name}" brand profile press coverage',
            )

        return queries

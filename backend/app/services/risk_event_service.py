"""
Risk Event business logic service.

Orchestrates risk event ingestion:
  1. Validate input
  2. Find or create merchant
  3. Compute derived fields (percentage_change)
  4. Persist to database
  5. Return the created event

This service does NOT trigger the investigation pipeline.
Day 1 design is: INGEST → STORE → RETURN.
The investigation pipeline will be connected in a later phase.
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from app.core.exceptions import DatabaseError, RiskEventValidationError
from app.core.logging import get_logger
from app.repositories import merchant_repository, risk_event_repository
from app.schemas.risk_event import (
    RiskEventCreate,
    RiskEventResponse,
    RiskEventStatus,
)

logger = get_logger("risk_event_service")


def ingest_risk_event(event_input: RiskEventCreate) -> RiskEventResponse:
    """
    Ingest a new risk event.

    This is the primary entry point for risk event creation.
    It validates, normalizes, and persists the event.

    Args:
        event_input: Validated risk event creation data.

    Returns:
        RiskEventResponse with the persisted event data.

    Raises:
        RiskEventValidationError: If business validation fails.
        DatabaseError: If persistence fails.
    """
    logger.info(
        "Ingesting risk event: merchant='{}', type='{}', source='{}'",
        event_input.merchant_name,
        event_input.anomaly_type.value,
        event_input.source.value,
    )

    # --- Step 1: Find or create merchant ---
    merchant = merchant_repository.find_or_create(
        merchant_name=event_input.merchant_name,
        merchant_domain=event_input.merchant_domain,
    )
    merchant_id = merchant["id"]

    # --- Step 2: Compute derived fields ---
    percentage_change = _compute_percentage_change(
        baseline=event_input.baseline_transaction_count,
        observed=event_input.observed_transaction_count,
    )

    # --- Step 3: Build database record ---
    event_data = {
        "merchant_id": merchant_id,
        "anomaly_type": event_input.anomaly_type.value,
        "occurred_at": event_input.occurred_at.isoformat(),
        "baseline_transaction_count": event_input.baseline_transaction_count,
        "observed_transaction_count": event_input.observed_transaction_count,
        "percentage_change": percentage_change,
        "transaction_amount": event_input.transaction_amount,
        "currency": event_input.currency,
        "risk_reason": event_input.risk_reason,
        "geographic_info": event_input.geographic_info,
        "source": event_input.source.value,
        "status": RiskEventStatus.PENDING.value,
    }

    # --- Step 4: Persist ---
    created_event = risk_event_repository.create(event_data)

    # --- Step 5: Build response ---
    response = RiskEventResponse(
        id=created_event["id"],
        merchant_id=merchant_id,
        merchant_name=event_input.merchant_name,
        merchant_domain=event_input.merchant_domain,
        anomaly_type=event_input.anomaly_type,
        occurred_at=event_input.occurred_at,
        baseline_transaction_count=event_input.baseline_transaction_count,
        observed_transaction_count=event_input.observed_transaction_count,
        percentage_change=percentage_change,
        transaction_amount=event_input.transaction_amount,
        currency=event_input.currency,
        risk_reason=event_input.risk_reason,
        geographic_info=event_input.geographic_info,
        source=event_input.source,
        status=RiskEventStatus.PENDING,
        created_at=created_event["created_at"],
        updated_at=created_event.get("updated_at"),
    )

    logger.info(
        "Risk event ingested successfully: id={}, merchant='{}', change={}%",
        response.id,
        event_input.merchant_name,
        percentage_change,
    )

    return response


def get_risk_event(event_id: UUID) -> RiskEventResponse:
    """
    Retrieve a risk event by ID.

    Args:
        event_id: UUID of the risk event.

    Returns:
        RiskEventResponse with event data.
    """
    event = risk_event_repository.get_by_id(event_id)
    merchant_info = event.get("merchants", {}) or {}

    return RiskEventResponse(
        id=event["id"],
        merchant_id=event["merchant_id"],
        merchant_name=merchant_info.get("merchant_name", "Unknown"),
        merchant_domain=merchant_info.get("merchant_domain"),
        anomaly_type=event["anomaly_type"],
        occurred_at=event["occurred_at"],
        baseline_transaction_count=event.get("baseline_transaction_count"),
        observed_transaction_count=event.get("observed_transaction_count"),
        percentage_change=event.get("percentage_change"),
        transaction_amount=event.get("transaction_amount"),
        currency=event.get("currency", "INR"),
        risk_reason=event.get("risk_reason"),
        geographic_info=event.get("geographic_info"),
        source=event["source"],
        status=event["status"],
        created_at=event["created_at"],
        updated_at=event.get("updated_at"),
    )


def list_risk_events(
    limit: int = 50,
    offset: int = 0,
    status: Optional[str] = None,
) -> tuple[list[RiskEventResponse], int]:
    """
    List risk events with optional filtering.

    Args:
        limit: Maximum results per page.
        offset: Pagination offset.
        status: Optional status filter.

    Returns:
        Tuple of (list of RiskEventResponse, total count).
    """
    events, total_count = risk_event_repository.list_events(
        limit=limit,
        offset=offset,
        status=status,
    )

    responses = []
    for event in events:
        merchant_info = event.get("merchants", {}) or {}
        responses.append(
            RiskEventResponse(
                id=event["id"],
                merchant_id=event["merchant_id"],
                merchant_name=merchant_info.get("merchant_name", "Unknown"),
                merchant_domain=merchant_info.get("merchant_domain"),
                anomaly_type=event["anomaly_type"],
                occurred_at=event["occurred_at"],
                baseline_transaction_count=event.get("baseline_transaction_count"),
                observed_transaction_count=event.get("observed_transaction_count"),
                percentage_change=event.get("percentage_change"),
                transaction_amount=event.get("transaction_amount"),
                currency=event.get("currency", "INR"),
                risk_reason=event.get("risk_reason"),
                geographic_info=event.get("geographic_info"),
                source=event["source"],
                status=event["status"],
                created_at=event["created_at"],
                updated_at=event.get("updated_at"),
            )
        )

    return responses, total_count


def _compute_percentage_change(
    baseline: Optional[int],
    observed: Optional[int],
) -> Optional[float]:
    """
    Compute percentage change between baseline and observed values.

    Returns None if either value is missing or baseline is zero.
    """
    if baseline is not None and observed is not None and baseline > 0:
        return round(((observed - baseline) / baseline) * 100, 2)
    return None

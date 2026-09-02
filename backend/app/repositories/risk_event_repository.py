"""
Risk Event data access layer.

Handles CRUD operations for the risk_events table via Supabase.
"""

from typing import Optional
from uuid import UUID

from app.core.exceptions import DatabaseError, ResourceNotFoundError
from app.core.logging import get_logger
from app.repositories.supabase_client import get_supabase_client

logger = get_logger("risk_event_repository")

TABLE = "risk_events"


def create(event_data: dict) -> dict:
    """
    Insert a new risk event into the database.

    Args:
        event_data: Dictionary of risk event fields matching the DB schema.

    Returns:
        The created risk event record dict.
    """
    try:
        client = get_supabase_client()
        response = (
            client.table(TABLE)
            .insert(event_data)
            .execute()
        )
        if response.data:
            event_id = response.data[0].get("id", "unknown")
            logger.info("Created risk event: id={}", event_id)
            return response.data[0]
        raise DatabaseError("Insert returned no data")
    except DatabaseError:
        raise
    except Exception as e:
        logger.error("Failed to create risk event: {}", str(e))
        raise DatabaseError(f"Failed to create risk event: {e}") from e


def get_by_id(event_id: UUID) -> dict:
    """
    Retrieve a risk event by its ID.

    Args:
        event_id: The risk event UUID.

    Returns:
        The risk event record dict.

    Raises:
        ResourceNotFoundError: If the event does not exist.
    """
    try:
        client = get_supabase_client()
        response = (
            client.table(TABLE)
            .select("*, merchants(merchant_name, merchant_domain)")
            .eq("id", str(event_id))
            .limit(1)
            .execute()
        )
        if response.data:
            return response.data[0]
        raise ResourceNotFoundError("risk_event", str(event_id))
    except ResourceNotFoundError:
        raise
    except Exception as e:
        logger.error("Failed to get risk event '{}': {}", event_id, str(e))
        raise DatabaseError(f"Failed to get risk event: {e}") from e


def list_events(
    limit: int = 50,
    offset: int = 0,
    status: Optional[str] = None,
) -> tuple[list[dict], int]:
    """
    List risk events with optional filtering.

    Args:
        limit: Maximum number of results (default 50).
        offset: Pagination offset.
        status: Optional status filter.

    Returns:
        Tuple of (list of event dicts, total count).
    """
    try:
        client = get_supabase_client()
        query = (
            client.table(TABLE)
            .select("*, merchants(merchant_name, merchant_domain)", count="exact")
        )

        if status:
            query = query.eq("status", status)

        response = (
            query.order("created_at", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
        )
        total_count = response.count if response.count is not None else len(response.data)
        return response.data, total_count
    except Exception as e:
        logger.error("Failed to list risk events: {}", str(e))
        raise DatabaseError(f"Failed to list risk events: {e}") from e


def update_status(event_id: UUID, new_status: str) -> dict:
    """
    Update the status of a risk event.

    Args:
        event_id: The risk event UUID.
        new_status: The new status value.

    Returns:
        The updated risk event record dict.
    """
    try:
        client = get_supabase_client()
        response = (
            client.table(TABLE)
            .update({"status": new_status, "updated_at": "now()"})
            .eq("id", str(event_id))
            .execute()
        )
        if response.data:
            logger.info("Updated risk event {} status to '{}'", event_id, new_status)
            return response.data[0]
        raise ResourceNotFoundError("risk_event", str(event_id))
    except ResourceNotFoundError:
        raise
    except Exception as e:
        logger.error("Failed to update risk event '{}': {}", event_id, str(e))
        raise DatabaseError(f"Failed to update risk event: {e}") from e

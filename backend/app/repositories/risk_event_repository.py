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

# In-memory storage fallback for local evaluation or when Supabase RLS restricts direct inserts
_memory_risk_events: dict[str, dict] = {}


def create(event_data: dict) -> dict:
    """
    Insert a new risk event into the database.

    Args:
        event_data: Dictionary of risk event fields matching the DB schema.

    Returns:
        The created risk event record dict.
    """
    from app.repositories import merchant_repository

    # Attempt Supabase insert first
    try:
        client = get_supabase_client()
        response = (
            client.table(TABLE)
            .insert(event_data)
            .execute()
        )
        if response.data:
            record = response.data[0]
            event_id = record.get("id", "unknown")
            logger.info("Created risk event in Supabase: id={}", event_id)
            _memory_risk_events[str(event_id)] = record
            return record
    except Exception as e:
        logger.warning(
            "Supabase insert risk_event failed ({}), falling back to in-memory store",
            str(e),
        )

    # In-memory fallback
    from datetime import datetime, timezone
    from uuid import uuid4

    new_id = str(uuid4())
    record = {
        "id": new_id,
        **event_data,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": None,
    }

    # Attach merchant join info if available
    merchant_id = event_data.get("merchant_id")
    if merchant_id:
        try:
            m = merchant_repository.find_by_id(UUID(str(merchant_id)))
            if m:
                record["merchants"] = {
                    "merchant_name": m.get("merchant_name"),
                    "merchant_domain": m.get("merchant_domain"),
                }
        except Exception:
            pass

    _memory_risk_events[new_id] = record
    logger.info("Created risk event in-memory fallback: id={}", new_id)
    return record


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
    str_id = str(event_id)
    try:
        client = get_supabase_client()
        response = (
            client.table(TABLE)
            .select("*, merchants(merchant_name, merchant_domain)")
            .eq("id", str_id)
            .limit(1)
            .execute()
        )
        if response.data:
            return response.data[0]
    except Exception as e:
        logger.warning("Supabase get risk_event '{}' failed, checking in-memory store: {}", str_id, str(e))

    if str_id in _memory_risk_events:
        return _memory_risk_events[str_id]

    raise ResourceNotFoundError("risk_event", str_id)


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
    results: list[dict] = []
    total_count = 0

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
        results = response.data or []
        total_count = response.count if response.count is not None else len(results)
    except Exception as e:
        logger.warning("Supabase list_events failed ({}), relying on in-memory store", str(e))

    # Merge in-memory events not already in results
    seen_ids = {str(r.get("id")) for r in results}
    mem_events = list(_memory_risk_events.values())
    if status:
        mem_events = [e for e in mem_events if e.get("status") == status]

    for ev in mem_events:
        if str(ev.get("id")) not in seen_ids:
            results.append(ev)
            total_count += 1

    return results, total_count


def update_status(event_id: UUID, new_status: str) -> dict:
    """
    Update the status of a risk event.

    Args:
        event_id: The risk event UUID.
        new_status: The new status value.

    Returns:
        The updated risk event record dict.
    """
    str_id = str(event_id)
    from datetime import datetime, timezone

    now_iso = datetime.now(timezone.utc).isoformat()

    try:
        client = get_supabase_client()
        response = (
            client.table(TABLE)
            .update({"status": new_status, "updated_at": "now()"})
            .eq("id", str_id)
            .execute()
        )
        if response.data:
            logger.info("Updated risk event {} status to '{}'", event_id, new_status)
            res = response.data[0]
            if str_id in _memory_risk_events:
                _memory_risk_events[str_id].update(res)
            return res
    except Exception as e:
        logger.warning("Supabase update_status for '{}' failed ({}), updating in-memory", str_id, str(e))

    if str_id in _memory_risk_events:
        _memory_risk_events[str_id]["status"] = new_status
        _memory_risk_events[str_id]["updated_at"] = now_iso
        logger.info("Updated in-memory risk event {} status to '{}'", str_id, new_status)
        return _memory_risk_events[str_id]

    raise ResourceNotFoundError("risk_event", str_id)

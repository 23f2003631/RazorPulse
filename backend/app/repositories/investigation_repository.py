"""
Investigation Repository.

Handles CRUD and persistence operations for the investigations table via Supabase.
"""

from datetime import datetime, timezone
import json
from typing import Optional
from uuid import UUID

from app.core.exceptions import DatabaseError, ResourceNotFoundError
from app.core.logging import get_logger
from app.repositories.supabase_client import get_supabase_client
from app.schemas.investigation import InvestigationStatus

logger = get_logger("investigation_repository")

TABLE = "investigations"

# In-memory storage fallback for local evaluation or when Supabase RLS restricts direct inserts
_memory_investigations: dict[str, dict] = {}


def create(risk_event_id: UUID) -> dict:
    """
    Create a new investigation record in PENDING state.
    """
    str_risk_id = str(risk_event_id)
    now_iso = datetime.now(timezone.utc).isoformat()
    data = {
        "risk_event_id": str_risk_id,
        "status": InvestigationStatus.PENDING.value,
        "started_at": now_iso,
    }

    try:
        client = get_supabase_client()
        response = client.table(TABLE).insert(data).execute()
        if response.data:
            inv_id = response.data[0]["id"]
            logger.info("Created investigation in Supabase: id={}, risk_event_id={}", inv_id, risk_event_id)
            _memory_investigations[str(inv_id)] = response.data[0]
            return response.data[0]
    except Exception as e:
        logger.warning(
            "Supabase insert investigation for risk_event {} failed ({}), falling back to in-memory store",
            risk_event_id,
            str(e),
        )

    # In-memory fallback
    from uuid import uuid4

    new_id = str(uuid4())
    record = {
        "id": new_id,
        "risk_event_id": str_risk_id,
        "status": InvestigationStatus.PENDING.value,
        "started_at": now_iso,
        "created_at": now_iso,
        "updated_at": None,
    }
    _memory_investigations[new_id] = record
    logger.info("Created investigation in-memory fallback: id={}, risk_event_id={}", new_id, risk_event_id)
    return record


def get_by_id(investigation_id: UUID) -> dict:
    """
    Retrieve an investigation record by ID.
    """
    str_id = str(investigation_id)
    try:
        client = get_supabase_client()
        response = (
            client.table(TABLE)
            .select("*, risk_events(*, merchants(*))")
            .eq("id", str_id)
            .limit(1)
            .execute()
        )
        if response.data:
            return response.data[0]
    except Exception as e:
        logger.warning("Supabase get investigation '{}' failed, checking in-memory store: {}", str_id, str(e))

    if str_id in _memory_investigations:
        inv = _memory_investigations[str_id]
        if "risk_events" not in inv and "risk_event_id" in inv:
            from app.repositories import risk_event_repository
            try:
                ev = risk_event_repository.get_by_id(UUID(str(inv["risk_event_id"])))
                inv["risk_events"] = ev
            except Exception:
                pass
        return inv

    raise ResourceNotFoundError("investigation", str_id)


def list_investigations(
    limit: int = 50,
    offset: int = 0,
    status: Optional[str] = None,
    risk_event_id: Optional[UUID] = None,
) -> tuple[list[dict], int]:
    """
    List investigation records with optional filtering.
    """
    results: list[dict] = []
    total_count = 0

    try:
        client = get_supabase_client()
        query = client.table(TABLE).select("*, risk_events(*, merchants(*))", count="exact")

        if status:
            query = query.eq("status", status)
        if risk_event_id:
            query = query.eq("risk_event_id", str(risk_event_id))

        response = (
            query.order("created_at", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
        )
        results = response.data or []
        total_count = response.count if response.count is not None else len(results)
    except Exception as e:
        logger.warning("Supabase list_investigations failed ({}), relying on in-memory store", str(e))

    # Merge in-memory investigations
    seen_ids = {str(r.get("id")) for r in results}
    mem_invs = list(_memory_investigations.values())
    if status:
        mem_invs = [i for i in mem_invs if i.get("status") == status]
    if risk_event_id:
        mem_invs = [i for i in mem_invs if str(i.get("risk_event_id")) == str(risk_event_id)]

    for inv in mem_invs:
        if str(inv.get("id")) not in seen_ids:
            results.append(inv)
            total_count += 1

    return results, total_count


def update_status(
    investigation_id: UUID,
    status: InvestigationStatus,
    error_stage: Optional[str] = None,
    error_message: Optional[str] = None,
) -> dict:
    """
    Update the investigation lifecycle status.
    """
    str_id = str(investigation_id)
    now_iso = datetime.now(timezone.utc).isoformat()
    update_data = {
        "status": status.value,
        "updated_at": now_iso,
    }
    if status == InvestigationStatus.COMPLETED:
        update_data["completed_at"] = now_iso
    if error_stage:
        update_data["error_stage"] = error_stage
    if error_message:
        update_data["error_message"] = error_message

    try:
        client = get_supabase_client()
        response = (
            client.table(TABLE)
            .update(update_data)
            .eq("id", str_id)
            .execute()
        )
        if response.data:
            logger.info("Updated investigation {} status to {}", investigation_id, status.value)
            res = response.data[0]
            if str_id in _memory_investigations:
                _memory_investigations[str_id].update(res)
            return res
    except Exception as e:
        logger.warning("Supabase update_status for investigation '{}' failed ({}), updating in-memory", str_id, str(e))

    if str_id in _memory_investigations:
        _memory_investigations[str_id].update(update_data)
        logger.info("Updated in-memory investigation {} status to {}", str_id, status.value)
        return _memory_investigations[str_id]

    raise ResourceNotFoundError("investigation", str_id)


def update_results(
    investigation_id: UUID,
    eci_score: int,
    eci_band: str,
    eci_version: str,
    evidence_count: int,
    search_queries: list[dict],
    eci_breakdown: dict,
    dossier: dict,
    evidence_items: list[dict],
    verification_items: list[dict],
) -> dict:
    """
    Persist completed investigation outputs to Supabase.
    """
    str_id = str(investigation_id)
    now_iso = datetime.now(timezone.utc).isoformat()
    update_data = {
        "status": InvestigationStatus.COMPLETED.value,
        "eci_score": eci_score,
        "eci_band": eci_band,
        "eci_version": eci_version,
        "evidence_count": evidence_count,
        "search_queries": search_queries,
        "eci_breakdown": eci_breakdown,
        "dossier": dossier,
        "evidence_items": evidence_items,
        "verification_items": verification_items,
        "completed_at": now_iso,
        "updated_at": now_iso,
    }

    try:
        client = get_supabase_client()
        response = (
            client.table(TABLE)
            .update(update_data)
            .eq("id", str_id)
            .execute()
        )
        if response.data:
            logger.info(
                "Persisted completed results for investigation {}: ECI={}",
                investigation_id,
                eci_score,
            )
            res = response.data[0]
            if str_id in _memory_investigations:
                _memory_investigations[str_id].update(res)
            return res
    except Exception as e:
        logger.warning("Supabase update_results for investigation '{}' failed ({}), updating in-memory", str_id, str(e))

    if str_id in _memory_investigations:
        _memory_investigations[str_id].update(update_data)
        logger.info("Persisted in-memory completed results for investigation {}: ECI={}", str_id, eci_score)
        return _memory_investigations[str_id]

    raise ResourceNotFoundError("investigation", str_id)

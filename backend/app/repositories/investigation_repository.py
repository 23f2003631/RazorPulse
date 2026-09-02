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


def create(risk_event_id: UUID) -> dict:
    """
    Create a new investigation record in PENDING state.
    """
    try:
        client = get_supabase_client()
        data = {
            "risk_event_id": str(risk_event_id),
            "status": InvestigationStatus.PENDING.value,
            "started_at": datetime.now(timezone.utc).isoformat(),
        }
        response = client.table(TABLE).insert(data).execute()
        if response.data:
            inv_id = response.data[0]["id"]
            logger.info("Created investigation: id={}, risk_event_id={}", inv_id, risk_event_id)
            return response.data[0]
        raise DatabaseError("Insert investigation returned no data")
    except DatabaseError:
        raise
    except Exception as e:
        logger.error("Failed to create investigation for risk event {}: {}", risk_event_id, str(e))
        raise DatabaseError(f"Failed to create investigation: {e}") from e


def get_by_id(investigation_id: UUID) -> dict:
    """
    Retrieve an investigation record by ID.
    """
    try:
        client = get_supabase_client()
        response = (
            client.table(TABLE)
            .select("*, risk_events(*, merchants(*))")
            .eq("id", str(investigation_id))
            .limit(1)
            .execute()
        )
        if response.data:
            return response.data[0]
        raise ResourceNotFoundError("investigation", str(investigation_id))
    except ResourceNotFoundError:
        raise
    except Exception as e:
        logger.error("Failed to get investigation '{}': {}", investigation_id, str(e))
        raise DatabaseError(f"Failed to get investigation: {e}") from e


def list_investigations(
    limit: int = 50,
    offset: int = 0,
    status: Optional[str] = None,
    risk_event_id: Optional[UUID] = None,
) -> tuple[list[dict], int]:
    """
    List investigation records with optional filtering.
    """
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
        total_count = response.count if response.count is not None else len(response.data)
        return response.data, total_count
    except Exception as e:
        logger.error("Failed to list investigations: {}", str(e))
        raise DatabaseError(f"Failed to list investigations: {e}") from e


def update_status(
    investigation_id: UUID,
    status: InvestigationStatus,
    error_stage: Optional[str] = None,
    error_message: Optional[str] = None,
) -> dict:
    """
    Update the investigation lifecycle status.
    """
    try:
        client = get_supabase_client()
        update_data = {
            "status": status.value,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        if status == InvestigationStatus.COMPLETED:
            update_data["completed_at"] = datetime.now(timezone.utc).isoformat()
        if error_stage:
            update_data["error_stage"] = error_stage
        if error_message:
            update_data["error_message"] = error_message

        response = (
            client.table(TABLE)
            .update(update_data)
            .eq("id", str(investigation_id))
            .execute()
        )
        if response.data:
            logger.info("Updated investigation {} status to {}", investigation_id, status.value)
            return response.data[0]
        raise ResourceNotFoundError("investigation", str(investigation_id))
    except ResourceNotFoundError:
        raise
    except Exception as e:
        logger.error("Failed to update status for investigation '{}': {}", investigation_id, str(e))
        raise DatabaseError(f"Failed to update investigation status: {e}") from e


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
    try:
        client = get_supabase_client()
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
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        response = (
            client.table(TABLE)
            .update(update_data)
            .eq("id", str(investigation_id))
            .execute()
        )
        if response.data:
            logger.info(
                "Persisted completed results for investigation {}: ECI={}",
                investigation_id,
                eci_score,
            )
            return response.data[0]
        raise ResourceNotFoundError("investigation", str(investigation_id))
    except ResourceNotFoundError:
        raise
    except Exception as e:
        logger.error("Failed to persist results for investigation '{}': {}", investigation_id, str(e))
        raise DatabaseError(f"Failed to persist investigation results: {e}") from e

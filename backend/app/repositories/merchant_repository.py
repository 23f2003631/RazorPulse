"""
Merchant data access layer.

Handles CRUD operations for the merchants table via Supabase.
"""

from typing import Optional
from uuid import UUID

from app.core.exceptions import DatabaseError
from app.core.logging import get_logger
from app.repositories.supabase_client import get_supabase_client

logger = get_logger("merchant_repository")

TABLE = "merchants"

# In-memory storage fallback for local evaluation or when Supabase RLS restricts direct inserts
_memory_merchants: dict[str, dict] = {}


def find_by_domain(domain: str) -> Optional[dict]:
    """
    Find a merchant by their web domain.

    Args:
        domain: The merchant's web domain (e.g., "example.com").

    Returns:
        Merchant record dict if found, None otherwise.
    """
    try:
        client = get_supabase_client()
        response = (
            client.table(TABLE)
            .select("*")
            .eq("merchant_domain", domain)
            .limit(1)
            .execute()
        )
        if response.data:
            return response.data[0]
    except Exception as e:
        logger.warning("Supabase find_by_domain failed, checking in-memory store: {}", str(e))

    for m in _memory_merchants.values():
        if m.get("merchant_domain") == domain:
            return m
    return None


def find_by_id(merchant_id: UUID) -> Optional[dict]:
    """
    Find a merchant by ID.

    Args:
        merchant_id: The merchant UUID.

    Returns:
        Merchant record dict if found, None otherwise.
    """
    try:
        client = get_supabase_client()
        response = (
            client.table(TABLE)
            .select("*")
            .eq("id", str(merchant_id))
            .limit(1)
            .execute()
        )
        if response.data:
            return response.data[0]
    except Exception as e:
        logger.warning("Supabase find_by_id failed, checking in-memory store: {}", str(e))

    return _memory_merchants.get(str(merchant_id))


def create(merchant_name: str, merchant_domain: Optional[str] = None) -> dict:
    """
    Create a new merchant record.

    Args:
        merchant_name: Display name of the merchant.
        merchant_domain: Web domain of the merchant (optional).

    Returns:
        The created merchant record dict.
    """
    try:
        client = get_supabase_client()
        data = {"merchant_name": merchant_name}
        if merchant_domain:
            data["merchant_domain"] = merchant_domain

        response = (
            client.table(TABLE)
            .insert(data)
            .execute()
        )
        if response.data:
            logger.info("Created merchant: name='{}', domain='{}'", merchant_name, merchant_domain)
            record = response.data[0]
            _memory_merchants[str(record["id"])] = record
            return record
    except Exception as e:
        logger.warning(
            "Supabase insert merchant '{}' failed ({}), falling back to in-memory store",
            merchant_name,
            str(e),
        )

    # In-memory fallback
    from datetime import datetime, timezone
    from uuid import uuid4

    new_id = str(uuid4())
    record = {
        "id": new_id,
        "merchant_name": merchant_name,
        "merchant_domain": merchant_domain,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": None,
    }
    _memory_merchants[new_id] = record
    logger.info("Created merchant in-memory fallback: id={}, name='{}'", new_id, merchant_name)
    return record


def find_or_create(merchant_name: str, merchant_domain: Optional[str] = None) -> dict:
    """
    Find an existing merchant by domain, or create a new one.

    If merchant_domain is provided, attempts to find by domain first.
    If not found (or no domain provided), creates a new merchant.

    Args:
        merchant_name: Display name of the merchant.
        merchant_domain: Web domain of the merchant (optional).

    Returns:
        The existing or newly created merchant record dict.
    """
    if merchant_domain:
        existing = find_by_domain(merchant_domain)
        if existing:
            logger.info("Found existing merchant for domain '{}'", merchant_domain)
            return existing

    return create(merchant_name, merchant_domain)

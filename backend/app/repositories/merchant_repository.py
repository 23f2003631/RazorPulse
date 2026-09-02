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
        return None
    except Exception as e:
        logger.error("Failed to find merchant by domain '{}': {}", domain, str(e))
        raise DatabaseError(f"Failed to find merchant: {e}") from e


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
        return None
    except Exception as e:
        logger.error("Failed to find merchant by ID '{}': {}", merchant_id, str(e))
        raise DatabaseError(f"Failed to find merchant: {e}") from e


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
            return response.data[0]
        raise DatabaseError("Insert returned no data")
    except DatabaseError:
        raise
    except Exception as e:
        logger.error("Failed to create merchant '{}': {}", merchant_name, str(e))
        raise DatabaseError(f"Failed to create merchant: {e}") from e


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

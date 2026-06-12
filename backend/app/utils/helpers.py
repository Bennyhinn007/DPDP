"""
Utility Helpers.

Common functions used across the application.
"""

import hashlib
import json
import uuid
from datetime import datetime, timezone


def generate_uuid() -> str:
    """Generate a new UUID v4 string."""
    return str(uuid.uuid4())


def utc_now() -> str:
    """Get current UTC timestamp as ISO string."""
    return datetime.now(timezone.utc).isoformat()


def utc_now_datetime() -> datetime:
    """Get current UTC datetime object."""
    return datetime.now(timezone.utc)


def compute_sha256(data: dict, exclude_fields: list[str] = None) -> str:
    """
    Compute SHA-256 hash of a dictionary.

    Args:
        data: Dictionary to hash
        exclude_fields: Field names to exclude from hashing

    Returns:
        Hex-encoded SHA-256 hash
    """
    if exclude_fields is None:
        exclude_fields = [
            "_id", "created_at", "updated_at", "updated_by",
            "verification_hash", "blockchain_tx_ref",
            "blockchain_anchor_id", "version",
        ]

    hashable = {k: v for k, v in data.items() if k not in exclude_fields}
    canonical = json.dumps(hashable, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

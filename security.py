import hashlib
from datetime import datetime
from typing import Optional


def sha256_hex(data: bytes) -> str:
    """Return SHA-256 hash of raw bytes as hex string."""
    return hashlib.sha256(data).hexdigest()


def hash_block(
    action: str,
    file_hash: str,
    timestamp: datetime,
    previous_hash: Optional[str],
) -> str:
    """
    Deterministically hash a custody block.

    We concatenate critical fields so any change becomes detectable.
    """
    prev = previous_hash or "GENESIS"
    payload = f"{action}|{file_hash}|{timestamp.isoformat()}|{prev}".encode("utf-8")
    return sha256_hex(payload)


"""
Fingerprint utility for generating stable cache keys.

Provides compute_fingerprint() for creating SHA256 hashes of payloads,
used for caching AI content and Maps API responses.
"""

import hashlib
import json
from typing import Any


def compute_fingerprint(payload: Any) -> str:
    """
    Compute stable SHA256 fingerprint of a payload.

    The fingerprint is deterministic and independent of key ordering in dicts.
    Used for caching AI-generated content and Maps API responses.

    Args:
        payload: Any JSON-serializable data structure

    Returns:
        Hex-encoded SHA256 hash (64 characters)

    Examples:
        >>> compute_fingerprint({"a": 1, "b": 2})
        'f1d2d2f924e986ac86fdf7b36c94bcdf32beec15'
        >>> compute_fingerprint({"b": 2, "a": 1})  # Same hash, different order
        'f1d2d2f924e986ac86fdf7b36c94bcdf32beec15'
    """
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

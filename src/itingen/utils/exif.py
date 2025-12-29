"""
EXIF metadata utilities for reading and writing metadata to JPEG images.

This module provides functions to embed and extract JSON metadata in JPEG
images using EXIF fields. Metadata is stored with a "SCFTH:" prefix in:
- UserComment field (tag 37510) for machine-readable JSON
- ImageDescription field (tag 270) for human-readable description

AIDEV-NOTE: EXIF metadata used for AI-generated image provenance tracking
"""

import json
import os
from typing import Any, Dict, Optional


def _stable_json_dumps(obj: Any) -> str:
    """Serialize object to stable JSON string (sorted keys, no whitespace)."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def read_exif_metadata(img_path: str) -> Optional[Dict[str, Any]]:
    """
    Read metadata from JPEG EXIF fields.

    Looks for JSON metadata in UserComment (tag 37510) or ImageDescription
    (tag 270) with "SCFTH:" prefix. Returns parsed JSON dict or None.

    Args:
        img_path: Path to JPEG image file

    Returns:
        Parsed metadata dict or None if not found/invalid

    Examples:
        >>> metadata = read_exif_metadata("image.jpg")
        >>> if metadata:
        ...     print(metadata["fingerprint"])
    """
    if not img_path or not os.path.exists(img_path):
        return None

    try:
        from PIL import Image  # type: ignore

        im = Image.open(img_path)
        exif = im.getexif()
        if not exif:
            return None

        # Try UserComment (37510) first, fallback to ImageDescription (270)
        raw = exif.get(37510) or exif.get(270)
        if raw is None:
            return None

        # Convert bytes to string if needed
        if isinstance(raw, bytes):
            try:
                raw_s = raw.decode("utf-8", errors="ignore")
            except Exception:
                raw_s = ""
        else:
            raw_s = str(raw)

        # Must have SCFTH: prefix
        if not raw_s.startswith("SCFTH:"):
            return None

        # Parse JSON after prefix
        json_str = raw_s[6:]  # Remove "SCFTH:" prefix
        try:
            metadata = json.loads(json_str)
            return metadata
        except json.JSONDecodeError:
            return None

    except Exception:
        return None


def write_exif_metadata(*, img_path: str, meta: Dict[str, Any], title: str = "Itinerary Image") -> bool:
    """
    Write metadata to JPEG EXIF fields.

    Embeds metadata in UserComment (37510) as machine-readable JSON and
    ImageDescription (270) as human-readable summary. Both use "SCFTH:" prefix.

    Args:
        img_path: Path to JPEG image file
        meta: Metadata dictionary to embed
        title: Title prefix for ImageDescription

    Returns:
        True if successful, False otherwise

    Examples:
        >>> meta = {"fingerprint": "abc123", "model": "gemini"}
        >>> success = write_exif_metadata(img_path="image.jpg", meta=meta)
    """
    if not img_path or not os.path.exists(img_path):
        return False

    try:
        from PIL import Image  # type: ignore

        im = Image.open(img_path)
        exif = im.getexif()
        if exif is None:
            return False

        # Serialize metadata to JSON with SCFTH: prefix
        meta_s = "SCFTH:" + _stable_json_dumps(meta)

        # UserComment: machine-readable JSON (kept small to avoid truncation)
        exif[37510] = meta_s

        # ImageDescription: human-readable summary for Preview.app
        fp = str(meta.get("fingerprint_sha256") or "").strip()
        pm = str(meta.get("event_model") or "").strip()
        ar = str(meta.get("aspect_ratio") or "").strip()
        pv = str(meta.get("prompt_preview") or "").strip()
        exif[270] = f"{title} | model={pm} | ar={ar} | fp={fp} | {pv}".strip()

        # Save image with updated EXIF
        im.save(img_path, format="JPEG", quality=92, optimize=True, exif=exif.tobytes())
        return True

    except Exception:
        return False

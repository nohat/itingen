"""Duration parsing and formatting utilities.

AIDEV-DECISION: duration_seconds is the canonical representation throughout the system.
- All sources (manual events, APIs) normalize to duration_seconds (int)
- Renderers format duration_seconds for display using format_duration()
- This prevents multiple parallel representations and ensures consistency

Why this matters:
- Manual events specify: duration: "1h30m"
- Google Maps API returns: duration_text: "1 hour 30 mins"
- Without normalization, every consumer needs fallback logic
- With normalization, there's exactly one way to represent duration
"""

import re
from typing import Optional


def parse_duration(duration_str: str) -> Optional[int]:
    """Parse duration string like '1h30m' or '2h' or '45m' into seconds.

    Args:
        duration_str: Duration in format like "1h30m", "2h", "45m", "1h 30m"

    Returns:
        Total seconds, or None if empty/whitespace

    Raises:
        ValueError: If format is invalid

    Examples:
        >>> parse_duration("1h30m")
        5400
        >>> parse_duration("2h")
        7200
        >>> parse_duration("45m")
        2700
        >>> parse_duration("")
        None
    """
    if not duration_str or not duration_str.strip():
        return None

    duration_str = duration_str.strip()

    # Match pattern: optional hours (Xh) and optional minutes (Ym)
    # Allow optional spaces between components
    pattern = r'^(?:(\d+)\s*h)?\s*(?:(\d+)\s*m)?$'
    match = re.match(pattern, duration_str, re.IGNORECASE)

    if not match:
        raise ValueError(f"Invalid duration format: '{duration_str}'. Expected format like '1h30m', '2h', or '45m'")

    hours_str, minutes_str = match.groups()

    # Must have at least hours or minutes
    if not hours_str and not minutes_str:
        raise ValueError(f"Invalid duration format: '{duration_str}'. Must specify hours and/or minutes")

    hours = int(hours_str) if hours_str else 0
    minutes = int(minutes_str) if minutes_str else 0

    return hours * 3600 + minutes * 60


def format_duration(seconds: Optional[int]) -> Optional[str]:
    """Format seconds into human-readable duration like '1h 30m'.

    Args:
        seconds: Total seconds, or None

    Returns:
        Formatted string like "1h 30m", "2h", "45m", or None if input is None

    Examples:
        >>> format_duration(5400)
        '1h 30m'
        >>> format_duration(7200)
        '2h'
        >>> format_duration(2700)
        '45m'
        >>> format_duration(None)
        None
    """
    if seconds is None:
        return None

    if seconds == 0:
        return "0m"

    # Round to nearest minute
    minutes_total = round(seconds / 60)

    hours = minutes_total // 60
    minutes = minutes_total % 60

    if hours > 0 and minutes > 0:
        return f"{hours}h {minutes}m"
    elif hours > 0:
        return f"{hours}h"
    else:
        return f"{minutes}m"

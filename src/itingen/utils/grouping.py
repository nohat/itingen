"""Event grouping utilities for timeline processing.

Provides shared logic for grouping events by date, used by both
TimelineProcessor (PDF rendering) and MarkdownEmitter.
"""

import datetime
from typing import Dict, List

from itingen.core.domain.events import Event


def group_events_by_date(events: List[Event]) -> Dict[str, List[Event]]:
    """Group events by date, extracting date from event fields.

    Determines the date for each event using the following priority:
    1. Explicit 'date' field (from extra fields)
    2. Parsed from 'time_utc' field
    3. Falls back to 'TBD' if neither available

    Args:
        events: List of Event objects to group

    Returns:
        Dictionary mapping date strings (YYYY-MM-DD or 'TBD') to lists of events.
        Events within each date maintain their original order.
    """
    events_by_date: Dict[str, List[Event]] = {}

    for event in events:
        date_str = _extract_date(event)

        if date_str not in events_by_date:
            events_by_date[date_str] = []
        events_by_date[date_str].append(event)

    return events_by_date


def _extract_date(event: Event) -> str:
    """Extract date string from an event.

    Args:
        event: Event to extract date from

    Returns:
        Date string in YYYY-MM-DD format, or 'TBD' if no date available
    """
    # Priority 1: Explicit date field
    date_str = getattr(event, "date", None)
    if date_str:
        return date_str

    # Priority 2: Parse from time_utc
    if event.time_utc:
        try:
            dt = datetime.datetime.fromisoformat(
                event.time_utc.replace("Z", "+00:00")
            )
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            pass

    # Fallback: TBD
    return "TBD"

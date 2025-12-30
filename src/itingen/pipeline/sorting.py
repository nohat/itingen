"""Chronological sorting logic for the pipeline.

AIDEV-NOTE: This hydrator ensures events are ordered by their UTC time.
Events without time information are moved to the end of the list.
"""

from typing import List
from itingen.core.base import BaseHydrator
from itingen.core.domain.events import Event


class ChronologicalSorter(BaseHydrator[Event]):
    """Sorts events chronologically by time_utc."""

    def hydrate(self, items: List[Event]) -> List[Event]:
        """Sort the given items by time_utc.
        
        Events with time_utc=None are placed after events with timestamps.
        Original relative order is preserved for events with identical or missing timestamps.
        """
        if not items:
            return []

        # Use a stable sort to preserve relative order for identical/missing times
        return sorted(
            items,
            key=lambda x: (x.time_utc is None, x.time_utc)
        )

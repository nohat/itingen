"""Hydrator for calculating wrap-up times between events.

AIDEV-NOTE: This hydrator looks ahead to the next event to determine when 
the current event should be wrapped up to ensure readiness for the next one.
"""

import datetime
from typing import List, Optional
from itingen.core.base import BaseHydrator
from itingen.core.domain.events import Event


class WrapUpHydrator(BaseHydrator[Event]):
    """Calculates wrap_up_time for events based on the next event's start time."""

    def hydrate(self, items: List[Event]) -> List[Event]:
        """Add wrap_up_time and be_ready text to events."""
        if not items:
            return []

        # Assuming items are already sorted chronologically
        for i, curr_ev in enumerate(items):
            # 1. Be ready logic (for current event)
            target_time = curr_ev.time_local or curr_ev.no_later_than
            if target_time:
                time_part = target_time
                if " " in target_time:
                    time_part = target_time.split(" ")[1]
                curr_ev.be_ready = f"Be ready by {time_part} for this."

            # 2. Wrap-up logic (look ahead)
            if i < len(items) - 1:
                next_ev = items[i+1]
                next_t = next_ev.time_local or next_ev.no_later_than
                if next_t:
                    time_part = next_t
                    if " " in next_t:
                        time_part = next_t.split(" ")[1]
                    curr_ev.wrap_up_time = time_part
                    curr_ev.next_event_title = next_ev.event_heading or next_ev.description or "your next event"

        return items

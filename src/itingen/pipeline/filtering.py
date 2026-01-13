"""Person-specific filtering logic for the pipeline.

AIDEV-NOTE: This hydrator filters events based on the participants list ('who').
If an event has an empty 'who' list, it is considered generic and shown to everyone.
"""

from typing import List, Optional, TypeVar
from itingen.core.base import BaseHydrator
from itingen.core.domain.events import Event

T = TypeVar("T")


class PersonFilter(BaseHydrator[Event]):
    """Filters events to show only those relevant to a specific person."""

    def __init__(self, person_slug: Optional[str] = None):
        """Initialize with a person slug.
        
        Args:
            person_slug: The slug of the person to filter for. If None, no filtering is applied.
        """
        self.person_slug = person_slug

    def hydrate(self, items: List[T], context=None) -> List[T]:
        """Filter the given items.
        
        An event is kept if:
        1. person_slug is None (no filtering)
        2. The event's 'who' list is empty (generic event)
        3. The person_slug is in the event's 'who' list
        """
        if not self.person_slug or not items:
            return items

        return [
            item for item in items
            if not item.who or self.person_slug in item.who
        ]

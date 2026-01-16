"""Hydrator for generating transition descriptions between events.

AIDEV-NOTE: This hydrator uses a registry of transition patterns to describe
how to move from one event to the next. The registry allows trip-specific
transition logic to be plugged into the core pipeline.
"""

from typing import List, Optional, TypeVar
from itingen.core.base import BaseHydrator
from itingen.core.domain.events import Event
from itingen.pipeline.transitions import TransitionRegistry

T = TypeVar('T')


class TransitionHydrator(BaseHydrator[Event]):
    """Enriches events with descriptive transition logistics from the previous event.

    This hydrator uses a TransitionRegistry to find appropriate handlers for
    event kind pairs. If no specific handler is found, it falls back to a
    generic location-based transition description.
    """

    def __init__(self, registry: TransitionRegistry):
        """Initialize with a TransitionRegistry.

        Args:
            registry: Registry containing transition handlers for event kind pairs.
        """
        self.registry = registry

    def hydrate(self, items: List[Event], context=None) -> List[Event]:
        """Add transition descriptions to events based on their predecessor."""
        if not items:
            return []

        new_items = []
        prev_ev: Optional[Event] = None
        for ev in items:
            updates = {}
            if prev_ev is not None:
                # Only calculate if not already set (e.g. from source)
                if not ev.transition_from_prev:
                    transition = self._describe_transition(prev_ev, ev)
                    if transition:
                        updates["transition_from_prev"] = transition
            
            if updates:
                new_ev = ev.model_copy(update=updates)
            else:
                new_ev = ev
                
            new_items.append(new_ev)
            prev_ev = new_ev  # Use the newly created event as the previous event for the next iteration

        return new_items

    def _describe_transition(self, prev_ev: Event, ev: Event) -> Optional[str]:
        """Generate transition description using the registry.

        First tries to find a specific handler in the registry. If no handler
        is found, applies a generic location-based fallback.

        Args:
            prev_ev: The previous event.
            ev: The current event.

        Returns:
            Transition description string, or None if no description can be generated.
        """
        # Try registry first
        description = self.registry.describe(prev_ev, ev)
        if description is not None:
            return description

        # Generic fallback for any transition with locations
        prev_loc = (prev_ev.location or prev_ev.travel_to or "").strip()
        curr_loc = (ev.location or ev.travel_from or ev.travel_to or "").strip()

        if prev_loc and curr_loc:
            return f"Move from {prev_loc} to {curr_loc}."

        return None

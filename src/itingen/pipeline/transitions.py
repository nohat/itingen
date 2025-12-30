"""Plugin-based transition registry for itinerary events.

AIDEV-NOTE: This registry manages logic for describing transitions between
different types of events (e.g., drive -> lodging). It allows trip-specific
logic to be plugged into the core pipeline.
"""

from typing import List, Callable, Tuple, Any
from itingen.core.domain.events import Event


class TransitionRegistry:
    """Registry for event transition handlers."""

    def __init__(self):
        # List of (from_kind, to_kind, handler)
        self._patterns: List[Tuple[str, str, Callable[[Event, Event], str]]] = []

    def register(self, from_kind: str, to_kind: str, handler: Callable[[Event, Event], str]):
        """Register a transition handler for specific event kind pairs.
        
        Args:
            from_kind: The kind of the preceding event.
            to_kind: The kind of the current event.
            handler: A function that takes (prev_event, curr_event) and returns a string description.
        """
        self._patterns.append((from_kind, to_kind, handler))

    def describe(self, prev_event: Event, curr_event: Event) -> str:
        """Find a matching handler and generate a transition description.
        
        Args:
            prev_event: The preceding event.
            curr_event: The current event.
            
        Returns:
            The transition description string.
            
        Raises:
            ValueError: If no handler is found for the given pair of event kinds.
        """
        for from_kind, to_kind, handler in self._patterns:
            if prev_event.kind == from_kind and curr_event.kind == to_kind:
                return handler(prev_event, curr_event)
        
        raise ValueError(f"No transition handler for {prev_event.kind} -> {curr_event.kind}")

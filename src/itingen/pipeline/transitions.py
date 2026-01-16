"""Plugin-based transition registry for itinerary events.

AIDEV-NOTE: This registry manages logic for describing transitions between
different types of events (e.g., drive -> lodging). It allows trip-specific
logic to be plugged into the core pipeline.
"""

from typing import List, Callable, Tuple, Optional
from itingen.core.domain.events import Event


class TransitionRegistry:
    """Registry for event transition handlers.

    AIDEV-DECISION: describe() returns None instead of raising ValueError for
    unmatched patterns to allow optional transition logic in the pipeline.

    Supports wildcard patterns using "*" to match any event kind.
    """

    def __init__(self):
        # List of (from_kind, to_kind, handler)
        self._patterns: List[Tuple[str, str, Callable[[Event, Event], str]]] = []

    def register(self, from_kind: str, to_kind: str, handler: Callable[[Event, Event], str]):
        """Register a transition handler for specific event kind pairs.

        Kinds are normalized to lowercase for consistent matching.

        Args:
            from_kind: The kind of the preceding event. Use "*" to match any kind.
            to_kind: The kind of the current event. Use "*" to match any kind.
            handler: A function that takes (prev_event, curr_event) and returns a string description.
        """
        # Normalize registered kinds (except wildcard) for consistent matching
        norm_from = from_kind if from_kind == "*" else from_kind.strip().lower()
        norm_to = to_kind if to_kind == "*" else to_kind.strip().lower()
        self._patterns.append((norm_from, norm_to, handler))

    def describe(self, prev_event: Event, curr_event: Event) -> Optional[str]:
        """Find a matching handler and generate a transition description.

        Matches are attempted in registration order. Exact matches take precedence
        over wildcard matches when patterns are registered specific-first.

        Args:
            prev_event: The preceding event.
            curr_event: The current event.

        Returns:
            The transition description string, or None if no handler matches.
        """
        # Normalize kinds for matching (handle None, whitespace)
        prev_kind = (prev_event.kind or "").strip().lower()
        curr_kind = (curr_event.kind or "").strip().lower()

        for from_kind, to_kind, handler in self._patterns:
            # Check if this pattern matches (exact or wildcard)
            from_matches = from_kind == "*" or prev_kind == from_kind
            to_matches = to_kind == "*" or curr_kind == to_kind

            if from_matches and to_matches:
                return handler(prev_event, curr_event)

        return None

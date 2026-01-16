"""Tests for TransitionRegistry."""

import pytest
from itingen.core.domain.events import Event
from itingen.pipeline.transitions import TransitionRegistry


class TestTransitionRegistry:
    """Unit tests for TransitionRegistry."""

    @pytest.fixture
    def registry(self):
        """Create a TransitionRegistry instance."""
        return TransitionRegistry()

    def test_register_adds_handler(self, registry):
        """Register adds a handler for a kind pair."""
        def handler(prev, curr):
            return "Test transition"

        registry.register("drive", "lodging", handler)

        # Registry should have one pattern
        assert len(registry._patterns) == 1

    def test_describe_returns_matching_handler_result(self, registry):
        """Describe returns the result from matching handler."""
        def handler(prev, curr):
            return f"Move from {prev.location} to {curr.location}"

        registry.register("drive", "lodging", handler)

        prev_event = Event(kind="drive", location="Airport")
        curr_event = Event(kind="lodging", location="Hotel")

        result = registry.describe(prev_event, curr_event)

        assert result == "Move from Airport to Hotel"

    def test_describe_returns_none_when_no_match(self, registry):
        """Describe returns None when no handler matches."""
        prev_event = Event(kind="drive", location="Airport")
        curr_event = Event(kind="lodging", location="Hotel")

        result = registry.describe(prev_event, curr_event)

        assert result is None

    def test_describe_uses_first_matching_handler(self, registry):
        """Describe uses first matching handler when multiple match."""
        def handler1(prev, curr):
            return "First handler"

        def handler2(prev, curr):
            return "Second handler"

        registry.register("drive", "lodging", handler1)
        registry.register("drive", "lodging", handler2)

        prev_event = Event(kind="drive", location="Airport")
        curr_event = Event(kind="lodging", location="Hotel")

        result = registry.describe(prev_event, curr_event)

        assert result == "First handler"

    def test_describe_matches_exact_kinds(self, registry):
        """Describe only matches exact kind pairs."""
        def handler(prev, curr):
            return "Match"

        registry.register("drive", "lodging", handler)

        # Should not match different kinds
        result = registry.describe(
            Event(kind="ferry", location="Terminal"),
            Event(kind="lodging", location="Hotel")
        )
        assert result is None

        result = registry.describe(
            Event(kind="drive", location="Airport"),
            Event(kind="airport_buffer", location="Terminal")
        )
        assert result is None

    def test_register_multiple_patterns(self, registry):
        """Can register multiple transition patterns."""
        def handler1(prev, curr):
            return "Drive to lodging"

        def handler2(prev, curr):
            return "Ferry to lodging"

        registry.register("drive", "lodging", handler1)
        registry.register("ferry", "lodging", handler2)

        # Both should work
        result1 = registry.describe(
            Event(kind="drive", location="Airport"),
            Event(kind="lodging", location="Hotel")
        )
        assert result1 == "Drive to lodging"

        result2 = registry.describe(
            Event(kind="ferry", location="Terminal"),
            Event(kind="lodging", location="Hotel")
        )
        assert result2 == "Ferry to lodging"

    def test_handler_receives_correct_events(self, registry):
        """Handler receives the correct prev and curr events."""
        received_events = []

        def handler(prev, curr):
            received_events.append((prev, curr))
            return "Transition"

        registry.register("drive", "lodging", handler)

        prev_event = Event(kind="drive", location="Airport")
        curr_event = Event(kind="lodging", location="Hotel")

        registry.describe(prev_event, curr_event)

        assert len(received_events) == 1
        assert received_events[0][0] == prev_event
        assert received_events[0][1] == curr_event

    def test_wildcard_from_kind_matches_any(self, registry):
        """Wildcard '*' for from_kind matches any event kind."""
        def handler(prev, curr):
            return "Any to lodging"

        registry.register("*", "lodging", handler)

        # Should match any kind -> lodging
        result1 = registry.describe(
            Event(kind="drive", location="A"),
            Event(kind="lodging", location="B")
        )
        assert result1 == "Any to lodging"

        result2 = registry.describe(
            Event(kind="ferry", location="C"),
            Event(kind="lodging", location="D")
        )
        assert result2 == "Any to lodging"

    def test_wildcard_to_kind_matches_any(self, registry):
        """Wildcard '*' for to_kind matches any event kind."""
        def handler(prev, curr):
            return "Drive to any"

        registry.register("drive", "*", handler)

        # Should match drive -> any kind
        result1 = registry.describe(
            Event(kind="drive", location="A"),
            Event(kind="lodging", location="B")
        )
        assert result1 == "Drive to any"

        result2 = registry.describe(
            Event(kind="drive", location="C"),
            Event(kind="ferry", location="D")
        )
        assert result2 == "Drive to any"

    def test_specific_pattern_takes_precedence_over_wildcard(self, registry):
        """Specific patterns match before wildcard patterns."""
        def specific_handler(prev, curr):
            return "Specific drive to lodging"

        def wildcard_handler(prev, curr):
            return "Any to lodging"

        # Register specific pattern first
        registry.register("drive", "lodging", specific_handler)
        # Register wildcard pattern second
        registry.register("*", "lodging", wildcard_handler)

        # Specific pattern should match
        result = registry.describe(
            Event(kind="drive", location="Airport"),
            Event(kind="lodging", location="Hotel")
        )
        assert result == "Specific drive to lodging"

        # Wildcard should match other patterns
        result2 = registry.describe(
            Event(kind="ferry", location="Terminal"),
            Event(kind="lodging", location="Hotel")
        )
        assert result2 == "Any to lodging"

    def test_whitespace_normalization_in_kinds(self, registry):
        """Event kinds are normalized (whitespace, case) before matching."""
        def handler(prev, curr):
            return "Transition"

        registry.register("drive", "lodging", handler)

        # Whitespace should be normalized
        result = registry.describe(
            Event(kind="  drive  ", location="Airport"),
            Event(kind="  lodging  ", location="Hotel")
        )
        assert result == "Transition"

    def test_case_normalization_in_kinds(self, registry):
        """Event kinds are case-insensitive."""
        def handler(prev, curr):
            return "Transition"

        registry.register("drive", "lodging", handler)

        # Case should be normalized
        result = registry.describe(
            Event(kind="DRIVE", location="Airport"),
            Event(kind="LODGING", location="Hotel")
        )
        assert result == "Transition"

    def test_none_kind_normalized_to_empty_string(self, registry):
        """None kinds are normalized to empty string."""
        def handler(prev, curr):
            return "Transition"

        # Register handler for empty string kinds
        registry.register("", "", handler)

        result = registry.describe(
            Event(kind=None, location="A"),
            Event(kind=None, location="B")
        )
        assert result == "Transition"

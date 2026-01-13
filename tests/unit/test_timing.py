"""Tests for WrapUpHydrator."""

import pytest
from itingen.core.domain.events import Event
from itingen.pipeline.timing import WrapUpHydrator


class TestWrapUpHydrator:
    """Unit tests for WrapUpHydrator."""

    @pytest.fixture
    def hydrator(self):
        """Create a WrapUpHydrator instance."""
        return WrapUpHydrator()

    def test_hydrate_empty_list(self, hydrator):
        """Returns empty list for empty input."""
        result = hydrator.hydrate([])
        assert result == []

    def test_hydrate_single_event_with_time_local(self, hydrator):
        """Single event with time_local gets be_ready but no wrap_up."""
        event = Event(
            kind="drive",
            time_local="2024-01-15 09:00",
            location="Hotel"
        )
        
        result = hydrator.hydrate([event])
        
        assert len(result) == 1
        assert result[0].be_ready == "Be ready by 09:00 for this."
        assert getattr(result[0], 'wrap_up_time', None) is None
        assert getattr(result[0], 'next_event_title', None) is None

    def test_hydrate_single_event_with_no_later_than(self, hydrator):
        """Single event with no_later_than gets be_ready but no wrap_up."""
        event = Event(
            kind="drive",
            no_later_than="2024-01-15 10:30",
            location="Hotel"
        )
        
        result = hydrator.hydrate([event])
        
        assert len(result) == 1
        assert result[0].be_ready == "Be ready by 10:30 for this."
        assert getattr(result[0], 'wrap_up_time', None) is None
        assert getattr(result[0], 'next_event_title', None) is None

    def test_hydrate_single_event_no_time(self, hydrator):
        """Single event with no time gets no be_ready or wrap_up."""
        event = Event(
            kind="drive",
            location="Hotel"
        )
        
        result = hydrator.hydrate([event])
        
        assert len(result) == 1
        assert getattr(result[0], 'be_ready', None) is None
        assert getattr(result[0], 'wrap_up_time', None) is None
        assert getattr(result[0], 'next_event_title', None) is None

    def test_hydrate_two_events_with_times(self, hydrator):
        """Two events get both be_ready and wrap_up for first event."""
        events = [
            Event(
                kind="drive",
                time_local="2024-01-15 09:00",
                location="Hotel"
            ),
            Event(
                kind="flight_departure",
                time_local="2024-01-15 11:00",
                location="Airport"
            )
        ]
        
        result = hydrator.hydrate(events)
        
        assert len(result) == 2
        
        # First event gets both be_ready and wrap_up
        assert result[0].be_ready == "Be ready by 09:00 for this."
        assert getattr(result[0], 'wrap_up_time', None) == "11:00"
        assert getattr(result[0], 'next_event_title', None) == "your next event"
        
        # Second event gets only be_ready
        assert result[1].be_ready == "Be ready by 11:00 for this."
        assert getattr(result[1], 'wrap_up_time', None) is None
        assert getattr(result[1], 'next_event_title', None) is None

    def test_hydrate_two_events_mixed_time_fields(self, hydrator):
        """Events with mixed time field types."""
        events = [
            Event(
                kind="drive",
                no_later_than="2024-01-15 09:00",
                location="Hotel"
            ),
            Event(
                kind="flight_departure",
                time_local="2024-01-15 11:30",
                location="Airport"
            )
        ]
        
        result = hydrator.hydrate(events)
        
        assert len(result) == 2
        assert result[0].be_ready == "Be ready by 09:00 for this."
        assert getattr(result[0], 'wrap_up_time', None) == "11:30"
        assert result[1].be_ready == "Be ready by 11:30 for this."

    def test_hydrate_multiple_events_sequence(self, hydrator):
        """Multiple events get proper wrap-up chain."""
        events = [
            Event(kind="drive", time_local="2024-01-15 08:00", location="Hotel"),
            Event(kind="flight_departure", time_local="2024-01-15 10:00", location="Airport"),
            Event(kind="flight_arrival", time_local="2024-01-15 14:00", location="Destination"),
            Event(kind="drive", time_local="2024-01-15 15:00", location="Final Hotel")
        ]
        
        result = hydrator.hydrate(events)
        
        assert len(result) == 4
        
        # First event
        assert result[0].be_ready == "Be ready by 08:00 for this."
        assert getattr(result[0], 'wrap_up_time', None) == "10:00"
        assert getattr(result[0], 'next_event_title', None) == "your next event"
        
        # Second event
        assert result[1].be_ready == "Be ready by 10:00 for this."
        assert getattr(result[1], 'wrap_up_time', None) == "14:00"
        assert getattr(result[1], 'next_event_title', None) == "your next event"
        
        # Third event
        assert result[2].be_ready == "Be ready by 14:00 for this."
        assert getattr(result[2], 'wrap_up_time', None) == "15:00"
        assert getattr(result[2], 'next_event_title', None) == "your next event"
        
        # Last event
        assert result[3].be_ready == "Be ready by 15:00 for this."
        assert getattr(result[3], 'wrap_up_time', None) is None
        assert getattr(result[3], 'next_event_title', None) is None

    def test_hydrate_next_event_with_event_heading(self, hydrator):
        """Uses event_heading for next_event_title when available."""
        events = [
            Event(kind="drive", time_local="09:00", location="Hotel"),
            Event(
                kind="flight_departure",
                time_local="11:00",
                location="Airport",
                event_heading="Flight to Auckland"
            )
        ]
        
        result = hydrator.hydrate(events)
        
        assert getattr(result[0], 'next_event_title', None) == "Flight to Auckland"

    def test_hydrate_next_event_with_description(self, hydrator):
        """Uses description for next_event_title when no event_heading."""
        events = [
            Event(kind="drive", time_local="09:00", location="Hotel"),
            Event(
                kind="flight_departure",
                time_local="11:00",
                location="Airport",
                description="Morning flight to Auckland"
            )
        ]
        
        result = hydrator.hydrate(events)
        
        assert getattr(result[0], 'next_event_title', None) == "Morning flight to Auckland"

    def test_hydrate_next_event_fallback_title(self, hydrator):
        """Uses fallback title when no event_heading or description."""
        events = [
            Event(kind="drive", time_local="09:00", location="Hotel"),
            Event(kind="flight_departure", time_local="11:00", location="Airport")
        ]
        
        result = hydrator.hydrate(events)
        
        assert getattr(result[0], 'next_event_title', None) == "your next event"

    def test_hydrate_event_without_time_for_wrap_up(self, hydrator):
        """Next event without time doesn't get wrap_up."""
        events = [
            Event(kind="drive", time_local="09:00", location="Hotel"),
            Event(kind="flight_departure", location="Airport")  # No time
        ]
        
        result = hydrator.hydrate(events)
        
        assert result[0].be_ready == "Be ready by 09:00 for this."
        assert getattr(result[0], 'wrap_up_time', None) is None
        assert getattr(result[0], 'next_event_title', None) is None

    def test_hydrate_preserves_existing_attributes(self, hydrator):
        """Overwrites existing attributes (current implementation behavior)."""
        event = Event(
            kind="drive",
            time_local="09:00",
            location="Hotel",
            be_ready="Existing ready message"
        )
        
        result = hydrator.hydrate([event])
        
        # Current implementation overwrites existing be_ready
        assert result[0].be_ready == "Be ready by 09:00 for this."

    def test_hydrate_time_parsing_with_space(self, hydrator):
        """Correctly parses time from datetime string with space."""
        event = Event(
            kind="drive",
            time_local="2024-01-15 14:30:00",
            location="Hotel"
        )
        
        result = hydrator.hydrate([event])
        
        assert result[0].be_ready == "Be ready by 14:30:00 for this."

    def test_hydrate_time_parsing_without_space(self, hydrator):
        """Handles time string without space."""
        event = Event(
            kind="drive",
            time_local="14:30",
            location="Hotel"
        )
        
        result = hydrator.hydrate([event])
        
        assert result[0].be_ready == "Be ready by 14:30 for this."

    def test_hydrate_no_later_than_parsing(self, hydrator):
        """Correctly parses time from no_later_than field."""
        events = [
            Event(kind="drive", no_later_than="2024-01-15 09:00", location="Hotel"),
            Event(kind="flight", no_later_than="2024-01-15 11:30", location="Airport")
        ]
        
        result = hydrator.hydrate(events)
        
        assert result[0].be_ready == "Be ready by 09:00 for this."
        assert getattr(result[0], 'wrap_up_time', None) == "11:30"

    def test_hydrate_time_local_priority_over_no_later_than(self, hydrator):
        """Uses time_local when both time fields are present."""
        event = Event(
            kind="drive",
            time_local="2024-01-15 10:00",
            no_later_than="2024-01-15 09:00",
            location="Hotel"
        )
        
        result = hydrator.hydrate([event])
        
        assert result[0].be_ready == "Be ready by 10:00 for this."

    def test_hydrate_returns_new_objects(self, hydrator):
        """Verifies events are NOT modified in place (immutability)."""
        events = [
            Event(kind="drive", time_local="09:00", location="Hotel"),
            Event(kind="flight", time_local="11:00", location="Airport")
        ]
        
        original_ids = [id(ev) for ev in events]
        result = hydrator.hydrate(events)
        result_ids = [id(ev) for ev in result]
        
        # Should be different objects
        assert original_ids != result_ids
        assert result[0].be_ready == "Be ready by 09:00 for this."
        assert getattr(events[0], 'be_ready', None) is None

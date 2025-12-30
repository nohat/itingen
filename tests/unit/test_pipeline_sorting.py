"""Tests for chronological sorting logic in the pipeline."""

import pytest
from datetime import datetime
from itingen.core.domain.events import Event
from itingen.pipeline.sorting import ChronologicalSorter

@pytest.fixture
def unsorted_events():
    """Create a list of unsorted events."""
    return [
        Event(
            event_heading="Later Event",
            time_utc="2026-01-01T15:00:00Z",
            description="Should be second"
        ),
        Event(
            event_heading="Earlier Event",
            time_utc="2026-01-01T10:00:00Z",
            description="Should be first"
        ),
        Event(
            event_heading="No Time Event",
            description="Should be last"
        ),
        Event(
            event_heading="Latest Event",
            time_utc="2026-01-02T09:00:00Z",
            description="Should be fourth"
        ),
    ]

def test_chronological_sorter_sorts_correctly(unsorted_events):
    """Test that events are sorted chronologically by time_utc."""
    sorter = ChronologicalSorter()
    sorted_events = sorter.hydrate(unsorted_events)
    
    assert len(sorted_events) == 4
    assert sorted_events[0].event_heading == "Earlier Event"
    assert sorted_events[1].event_heading == "Later Event"
    assert sorted_events[2].event_heading == "Latest Event"
    assert sorted_events[3].event_heading == "No Time Event"

def test_chronological_sorter_handles_empty_list():
    """Test that sorter handles an empty list of events."""
    sorter = ChronologicalSorter()
    assert sorter.hydrate([]) == []

def test_chronological_sorter_handles_all_no_time():
    """Test that sorter handles events with no time information."""
    events = [
        Event(event_heading="A"),
        Event(event_heading="B"),
    ]
    sorter = ChronologicalSorter()
    sorted_events = sorter.hydrate(events)
    # Original order should be preserved if no times
    assert sorted_events[0].event_heading == "A"
    assert sorted_events[1].event_heading == "B"

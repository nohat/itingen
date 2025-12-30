"""Tests for person-specific filtering logic in the pipeline."""

import pytest
from itingen.core.domain.events import Event
from itingen.pipeline.filtering import PersonFilter

@pytest.fixture
def mixed_events():
    """Create a list of events with different participants."""
    return [
        Event(
            event_heading="Event for David",
            who=["david"],
            description="David only"
        ),
        Event(
            event_heading="Event for Everyone",
            who=[],
            description="Everyone"
        ),
        Event(
            event_heading="Event for Clara",
            who=["clara"],
            description="Clara only"
        ),
        Event(
            event_heading="Event for David and Diego",
            who=["david", "diego"],
            description="David and Diego"
        ),
    ]

def test_person_filter_filters_correctly_for_david(mixed_events):
    """Test that filter keeps only David's events and generic events."""
    filter_stage = PersonFilter(person_slug="david")
    filtered_events = filter_stage.hydrate(mixed_events)
    
    assert len(filtered_events) == 3
    headings = [e.event_heading for e in filtered_events]
    assert "Event for David" in headings
    assert "Event for Everyone" in headings
    assert "Event for David and Diego" in headings
    assert "Event for Clara" not in headings

def test_person_filter_filters_correctly_for_clara(mixed_events):
    """Test that filter keeps only Clara's events and generic events."""
    filter_stage = PersonFilter(person_slug="clara")
    filtered_events = filter_stage.hydrate(mixed_events)
    
    assert len(filtered_events) == 2
    headings = [e.event_heading for e in filtered_events]
    assert "Event for Clara" in headings
    assert "Event for Everyone" in headings
    assert "Event for David" not in headings

def test_person_filter_handles_none_person_slug(mixed_events):
    """Test that if no person_slug is provided, all events are returned."""
    filter_stage = PersonFilter(person_slug=None)
    filtered_events = filter_stage.hydrate(mixed_events)
    assert len(filtered_events) == 4

def test_person_filter_handles_empty_list():
    """Test that filter handles an empty list of events."""
    filter_stage = PersonFilter(person_slug="david")
    assert filter_stage.hydrate([]) == []

"""Tests for the plugin-based transition registry."""

import pytest
from itingen.core.domain.events import Event
from itingen.pipeline.transitions import TransitionRegistry

@pytest.fixture
def registry():
    """Create a transition registry."""
    return TransitionRegistry()

def test_registry_describe_simple_transition(registry):
    """Test registering and describing a simple transition."""
    def drive_to_hotel(prev, curr):
        return f"Drive from {prev.location} to {curr.location}"

    registry.register("drive", "lodging", drive_to_hotel)
    
    prev = Event(kind="drive", location="Airport")
    curr = Event(kind="lodging", location="Hotel")
    
    description = registry.describe(prev, curr)
    assert description == "Drive from Airport to Hotel"

def test_registry_returns_none_on_unhandled_transition(registry):
    """Test that registry returns None for unhandled transitions."""
    prev = Event(kind="unknown")
    curr = Event(kind="something")
    
    assert registry.describe(prev, curr) is None

def test_registry_multiple_handlers(registry):
    """Test that multiple handlers can coexist."""
    registry.register("A", "B", lambda p, c: "A to B")
    registry.register("C", "D", lambda p, c: "C to D")
    
    assert registry.describe(Event(kind="A"), Event(kind="B")) == "A to B"
    assert registry.describe(Event(kind="C"), Event(kind="D")) == "C to D"

def test_registry_first_match_wins(registry):
    """Test that the first registered matching handler is used."""
    registry.register("A", "B", lambda p, c: "First")
    registry.register("A", "B", lambda p, c: "Second")
    
    assert registry.describe(Event(kind="A"), Event(kind="B")) == "First"

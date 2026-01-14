"""Tests for AI-powered transition generation hydrator."""

import pytest
from unittest.mock import Mock, MagicMock
from itingen.core.domain.events import Event
from itingen.hydrators.ai.transitions import GeminiTransitionHydrator
from itingen.integrations.ai.gemini import GeminiClient
from itingen.hydrators.ai.cache import AiCache


@pytest.fixture
def mock_gemini_client():
    """Mock GeminiClient for testing."""
    client = Mock(spec=GeminiClient)
    client.generate_text = MagicMock(return_value="Walk from the ferry terminal to the car rental office, collect your rental car, and begin the scenic drive to Rotorua.")
    return client


@pytest.fixture
def temp_cache(tmp_path):
    """Temporary cache directory for testing."""
    return AiCache(tmp_path / "test_cache")


def test_gemini_transition_hydrator_generates_transition(mock_gemini_client):
    """Test that Gemini generates a valid transition."""
    hydrator = GeminiTransitionHydrator(client=mock_gemini_client, cache=None)
    
    prev_event = Event(
        kind="ferry",
        location="Auckland Ferry Terminal",
        travel_to="Waiheke Island",
        event_heading="Ferry to Waiheke",
        start_time="2026-01-15T09:00:00",
        end_time="2026-01-15T10:00:00"
    )
    curr_event = Event(
        kind="drive",
        location="Waiheke Island",
        travel_from="Matiatia Wharf",
        travel_to="Rotorua",
        event_heading="Drive to Rotorua",
        start_time="2026-01-15T10:00:00",
        end_time="2026-01-15T13:00:00"
    )
    
    events = [prev_event, curr_event]
    result = hydrator.hydrate(events)
    
    assert len(result) == 2
    assert result[1].transition_from_prev is not None
    assert len(result[1].transition_from_prev) > 10
    assert mock_gemini_client.generate_text.called


def test_gemini_transition_hydrator_uses_cache(mock_gemini_client, temp_cache):
    """Test that cache is used to avoid redundant API calls."""
    hydrator = GeminiTransitionHydrator(client=mock_gemini_client, cache=temp_cache)
    
    prev_event = Event(
        kind="ferry",
        location="Auckland Ferry Terminal",
        event_heading="Ferry",
        start_time="2026-01-15T09:00:00",
        end_time="2026-01-15T10:00:00"
    )
    curr_event = Event(
        kind="drive",
        location="Rotorua",
        event_heading="Drive",
        start_time="2026-01-15T10:00:00",
        end_time="2026-01-15T13:00:00"
    )
    
    # First call - should hit API
    events = [prev_event, curr_event]
    result1 = hydrator.hydrate(events)
    
    # Second call - should use cache
    result2 = hydrator.hydrate(events)
    
    assert result1[1].transition_from_prev == result2[1].transition_from_prev
    # API should only be called once (cached second time)
    assert mock_gemini_client.generate_text.call_count == 1


def test_gemini_transition_hydrator_respects_existing_transitions(mock_gemini_client):
    """Test that existing transitions are not overwritten."""
    hydrator = GeminiTransitionHydrator(client=mock_gemini_client)
    
    prev_event = Event(
        kind="ferry",
        location="Auckland",
        event_heading="Ferry",
        start_time="2026-01-15T09:00:00",
        end_time="2026-01-15T10:00:00"
    )
    curr_event = Event(
        kind="drive",
        location="Rotorua",
        event_heading="Drive",
        start_time="2026-01-15T10:00:00",
        end_time="2026-01-15T13:00:00",
        transition_from_prev="Custom transition text"
    )
    
    events = [prev_event, curr_event]
    result = hydrator.hydrate(events)
    
    # Should preserve existing transition
    assert result[1].transition_from_prev == "Custom transition text"
    # Should not call API
    assert not mock_gemini_client.generate_text.called


def test_gemini_transition_hydrator_empty_list(mock_gemini_client):
    """Test that empty list returns empty list."""
    hydrator = GeminiTransitionHydrator(client=mock_gemini_client)
    result = hydrator.hydrate([])
    assert result == []


def test_gemini_transition_hydrator_single_event(mock_gemini_client):
    """Test that single event has no transition."""
    hydrator = GeminiTransitionHydrator(client=mock_gemini_client)
    
    event = Event(
        kind="activity",
        location="Auckland",
        event_heading="Activity",
        start_time="2026-01-15T09:00:00",
        end_time="2026-01-15T10:00:00"
    )
    
    result = hydrator.hydrate([event])
    
    assert len(result) == 1
    assert result[0].transition_from_prev is None


def test_gemini_transition_hydrator_includes_driver_and_parking(mock_gemini_client):
    """Test that driver and parking info is included in prompt."""
    hydrator = GeminiTransitionHydrator(client=mock_gemini_client)
    
    prev_event = Event(
        kind="ferry",
        location="Auckland",
        event_heading="Ferry",
        start_time="2026-01-15T09:00:00",
        end_time="2026-01-15T10:00:00"
    )
    
    # Add driver and parking as extra attributes
    curr_event = Event(
        kind="drive",
        location="Rotorua",
        event_heading="Drive",
        start_time="2026-01-15T10:00:00",
        end_time="2026-01-15T13:00:00"
    )
    # Simulate driver/parking attributes (these would be in the actual Event model)
    curr_event_dict = curr_event.model_dump()
    curr_event_dict["driver"] = "John"
    curr_event_dict["parking"] = "on-site parking"
    curr_event_with_extras = Event(**curr_event_dict)
    
    events = [prev_event, curr_event_with_extras]
    hydrator.hydrate(events)
    
    # Check that generate_text was called with a prompt containing driver/parking
    call_args = mock_gemini_client.generate_text.call_args
    prompt = call_args[0][0]
    assert "John" in prompt or "Driver: John" in prompt
    assert "on-site parking" in prompt or "Parking instructions: on-site parking" in prompt


def test_gemini_transition_hydrator_cleans_quotes():
    """Test that response quotes are cleaned up."""
    client = Mock(spec=GeminiClient)
    # Return transition with quotes
    client.generate_text.return_value = '"Walk from the ferry to the car."'
    
    hydrator = GeminiTransitionHydrator(client=client)
    
    prev_event = Event(
        kind="ferry",
        location="Auckland",
        event_heading="Ferry",
        start_time="2026-01-15T09:00:00",
        end_time="2026-01-15T10:00:00"
    )
    curr_event = Event(
        kind="drive",
        location="Rotorua",
        event_heading="Drive",
        start_time="2026-01-15T10:00:00",
        end_time="2026-01-15T13:00:00"
    )
    
    events = [prev_event, curr_event]
    result = hydrator.hydrate(events)
    
    # Quotes should be stripped
    assert result[1].transition_from_prev == "Walk from the ferry to the car."
    assert '"' not in result[1].transition_from_prev

import pytest
import os
import yaml
import json
from pathlib import Path
from itingen.providers.file_provider import LocalFileProvider
from itingen.core.domain.events import Event
from itingen.core.domain.venues import Venue

@pytest.fixture
def trip_dir(tmp_path):
    """Create a temporary trip directory structure."""
    trip = tmp_path / "test_trip"
    events_dir = trip / "events"
    venues_dir = trip / "venues"
    events_dir.mkdir(parents=True)
    venues_dir.mkdir(parents=True)
    
    # Create config.yaml
    config = {
        "trip": {"name": "Test Trip"},
        "travelers": [{"name": "Alice", "slug": "alice"}]
    }
    with open(trip / "config.yaml", "w") as f:
        yaml.dump(config, f)
        
    # Create an event file
    event_md = """- date: 2025-12-29
- city: Auckland

### Event: Arrival
- kind: flight
- location: AKL Airport
- who: Alice
"""
    with open(events_dir / "2025-12-29.md", "w") as f:
        f.write(event_md)
        
    # Create a venue file
    venue_data = {
        "venue_id": "test-venue",
        "canonical_name": "Test Venue",
        "metadata": {
            "created_at": "2025-12-29T12:00:00Z",
            "updated_at": "2025-12-29T12:00:00Z"
        }
    }
    with open(venues_dir / "test-venue.json", "w") as f:
        json.dump(venue_data, f)
        
    return trip

def test_local_file_provider_load_venues_invalid_json(trip_dir):
    """Test that invalid JSON in a venue file raises an error."""
    invalid_json = trip_dir / "venues" / "invalid.json"
    with open(invalid_json, "w") as f:
        f.write("invalid json")
        
    provider = LocalFileProvider(trip_dir)
    with pytest.raises(json.JSONDecodeError):
        provider.get_venues()

def test_local_file_provider_load_venues_validation_error(trip_dir):
    """Test that invalid venue data (validation error) raises an error."""
    invalid_data = {"venue_id": "missing-fields"} # Missing required fields
    invalid_venue = trip_dir / "venues" / "invalid_venue.json"
    with open(invalid_venue, "w") as f:
        json.dump(invalid_data, f)
        
    provider = LocalFileProvider(trip_dir)
    # Pydantic raises ValidationError
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        provider.get_venues()

def test_local_file_provider_load_config(trip_dir):
    provider = LocalFileProvider(trip_dir)
    config = provider.get_config()
    assert config["trip"]["name"] == "Test Trip"

def test_local_file_provider_load_events(trip_dir):
    provider = LocalFileProvider(trip_dir)
    events = provider.get_events()
    assert len(events) == 1
    assert isinstance(events[0], Event)
    assert events[0].event_heading == "Arrival"
    assert events[0].location == "AKL Airport"
    # Verify day metadata was applied
    assert getattr(events[0], "date") == "2025-12-29"

def test_local_file_provider_load_venues(trip_dir):
    provider = LocalFileProvider(trip_dir)
    venues = provider.get_venues()
    assert "test-venue" in venues
    assert isinstance(venues["test-venue"], Venue)
    assert venues["test-venue"].canonical_name == "Test Venue"

def test_local_file_provider_invalid_dir():
    with pytest.raises(ValueError, match="Trip directory not found"):
        LocalFileProvider("/non/existent/path")

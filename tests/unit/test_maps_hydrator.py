import pytest
from unittest.mock import MagicMock, patch
from itingen.core.domain.events import Event
from itingen.hydrators.maps import MapsHydrator

@pytest.fixture
def mock_google_maps_client():
    with patch("itingen.hydrators.maps.GoogleMapsClient") as mock:
        yield mock.return_value

@pytest.fixture
def sample_events():
    return [
        Event(
            event_heading="Drive to Hotel",
            kind="drive",
            travel_from="Airport",
            travel_to="Park Hyatt",
            location="Tokyo"
        ),
        Event(
            event_heading="Dinner",
            kind="activity",
            location="Restaurant"
        ),
        Event(
            event_heading="Locked Drive",
            kind="drive",
            travel_from="Hotel",
            travel_to="Shrine",
            lock_duration=True
        )
    ]

def test_maps_hydrator_enriches_drive_events(mock_google_maps_client, sample_events):
    mock_google_maps_client.get_directions.return_value = {
        "duration_seconds": 1800,
        "duration_text": "30 mins",
        "distance_text": "15 km"
    }
    
    hydrator = MapsHydrator(api_key="fake-key")
    hydrated_events = hydrator.hydrate(sample_events)
    
    # Check first drive event was enriched
    drive_event = hydrated_events[0]
    assert drive_event.duration_seconds == 1800
    assert drive_event.duration_text == "30 mins"
    assert drive_event.distance_text == "15 km"
    assert drive_event.description == "Drive from Airport to Park Hyatt"
    
    # Check non-drive event was NOT enriched
    activity_event = hydrated_events[1]
    assert not hasattr(activity_event, "duration_seconds")
    
    # Check locked drive event was NOT enriched
    locked_drive = hydrated_events[2]
    assert not hasattr(locked_drive, "duration_seconds")
    
    # Verify client was called only once for the eligible drive
    mock_google_maps_client.get_directions.assert_called_once_with(
        origin="Airport",
        destination="Park Hyatt",
        mode="driving"
    )

def test_maps_hydrator_handles_missing_travel_fields(mock_google_maps_client):
    event = Event(kind="drive", event_heading="Drive with no fields")
    hydrator = MapsHydrator(api_key="fake-key")
    
    hydrated_events = hydrator.hydrate([event])
    
    assert hydrated_events[0] == event
    mock_google_maps_client.get_directions.assert_not_called()

def test_maps_hydrator_bubbles_exceptions(mock_google_maps_client):
    mock_google_maps_client.get_directions.side_effect = Exception("API Error")
    
    event = Event(kind="drive", travel_from="A", travel_to="B")
    hydrator = MapsHydrator(api_key="fake-key")
    
    with pytest.raises(Exception, match="API Error"):
        hydrator.hydrate([event])

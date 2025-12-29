import pytest
from unittest.mock import patch
from itingen.core.domain.events import Event
from itingen.hydrators.weather import WeatherHydrator

@pytest.fixture
def mock_weather_client():
    with patch("itingen.hydrators.weather.WeatherSparkClient") as mock:
        yield mock.return_value

@pytest.fixture
def sample_events():
    return [
        Event(
            event_heading="Visit Tokyo Tower",
            location="Tokyo Tower, Japan",
            time_utc="2025-01-01T10:00:00Z"
        ),
        Event(
            event_heading="No Location",
            time_utc="2025-01-01T10:00:00Z"
        ),
        Event(
            event_heading="No Time",
            location="Tokyo"
        )
    ]

def test_weather_hydrator_enriches_events(mock_weather_client, sample_events):
    mock_weather_client.get_typical_weather.return_value = {
        "high_temp_f": 45,
        "low_temp_f": 32,
        "conditions": "Clear"
    }
    
    hydrator = WeatherHydrator()
    hydrated_events = hydrator.hydrate(sample_events)
    
    # Check first event was enriched
    event = hydrated_events[0]
    assert event.weather_temp_high == 45
    assert event.weather_temp_low == 32
    assert event.weather_conditions == "Clear"
    
    # Check events with missing fields were NOT enriched
    assert not hasattr(hydrated_events[1], "weather_temp_high")
    assert not hasattr(hydrated_events[2], "weather_temp_high")
    
    # Verify client was called only once for the eligible event
    mock_weather_client.get_typical_weather.assert_called_once_with(
        "Tokyo Tower, Japan", "2025-01-01"
    )

def test_weather_hydrator_bubbles_exceptions(mock_weather_client):
    mock_weather_client.get_typical_weather.side_effect = Exception("Weather Error")
    
    event = Event(location="Tokyo", time_utc="2025-01-01T10:00:00Z")
    hydrator = WeatherHydrator()
    
    with pytest.raises(Exception, match="Weather Error"):
        hydrator.hydrate([event])

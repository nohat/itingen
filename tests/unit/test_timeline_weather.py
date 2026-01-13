"""Unit tests for weather aggregation in TimelineProcessor."""

from itingen.core.domain.events import Event
from itingen.rendering.timeline import TimelineProcessor

def test_timeline_processor_aggregates_weather():
    """Test that TimelineProcessor pulls weather data from events into TimelineDay."""
    processor = TimelineProcessor()
    
    events = [
        Event(
            event_heading="Event with Weather",
            date="2025-01-01",
            time_utc="2025-01-01T10:00:00Z",
            location="Tokyo",
            weather_temp_high=75.0,
            weather_temp_low=60.0,
            weather_conditions="Sunny"
        ),
        Event(
            event_heading="Event without Weather",
            date="2025-01-01",
            time_utc="2025-01-01T14:00:00Z",
            location="Tokyo"
        )
    ]
    
    days = processor.process(events)
    
    assert len(days) == 1
    day = days[0]
    assert day.weather_high == 75.0
    assert day.weather_low == 60.0
    assert day.weather_conditions == "Sunny"

def test_timeline_processor_no_weather():
    """Test that TimelineDay has None for weather if no events have it."""
    processor = TimelineProcessor()
    
    events = [
        Event(
            event_heading="No Weather",
            date="2025-01-01",
            time_utc="2025-01-01T10:00:00Z"
        )
    ]
    
    days = processor.process(events)
    
    assert len(days) == 1
    day = days[0]
    assert day.weather_high is None
    assert day.weather_low is None
    assert day.weather_conditions is None

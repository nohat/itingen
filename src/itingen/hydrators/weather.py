from typing import List, Optional
from itingen.core.base import BaseHydrator
from itingen.core.domain.events import Event
from itingen.integrations.weather.weatherspark import WeatherSparkClient

class WeatherHydrator(BaseHydrator[Event]):
    """Hydrator that enriches events with typical weather data.
    
    AIDEV-NOTE: Weather enrichment is non-critical; fails fast on logic errors 
    but should eventually handle transient provider failures gracefully.
    """

    def __init__(self, cache_dir: Optional[str] = None):
        """Initialize with optional cache directory."""
        self.client = WeatherSparkClient(cache_dir=cache_dir)

    def hydrate(self, items: List[Event]) -> List[Event]:
        """Enrich events with weather data based on location and date."""
        new_items = []
        for event in items:
            if not event.location or not event.time_utc:
                new_items.append(event)
                continue
            
            # Extract date from time_utc (ISO 8601)
            try:
                date_str = event.time_utc.split("T")[0]
                weather_data = self.client.get_typical_weather(event.location, date_str)
                
                if weather_data:
                    # Enrich event with weather fields
                    updates = {
                        "weather_temp_high": weather_data.get("high_temp_f"),
                        "weather_temp_low": weather_data.get("low_temp_f"),
                        "weather_conditions": weather_data.get("conditions")
                    }
                    new_items.append(event.model_copy(update=updates))
                else:
                    new_items.append(event)
            except Exception:
                # We follow the fail-fast principle for data integrity, 
                # but might allow weather to be missing if the provider is down.
                # For now, let it bubble up as per SPE orchestrator pattern.
                raise
                
        return new_items

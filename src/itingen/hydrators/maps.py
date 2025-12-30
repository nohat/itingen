from typing import List, Optional
from itingen.core.base import BaseHydrator
from itingen.core.domain.events import Event
from itingen.integrations.maps.google_maps import GoogleMapsClient

class MapsHydrator(BaseHydrator[Event]):
    """Hydrator that enriches events with Google Maps data (duration, distance).
    
    AIDEV-NOTE: Uses GoogleMapsClient with local caching to minimize API calls 
    and ensure deterministic builds when keys are missing.
    """

    def __init__(self, api_key: str, cache_dir: Optional[str] = None):
        """Initialize with Google Maps API key and optional cache directory."""
        self.client = GoogleMapsClient(api_key=api_key, cache_dir=cache_dir)

    def hydrate(self, items: List[Event]) -> List[Event]:
        """Enrich drive events with duration and distance from Google Maps."""
        for event in items:
            # Only hydrate drive events that don't have locked duration
            if event.kind != "drive" or getattr(event, "lock_duration", False):
                continue
            
            origin = event.travel_from
            destination = event.travel_to
            
            if not origin or not destination:
                # If travel fields are missing, try to use location
                # This is a bit brittle, but matches expected behavior for drives
                continue

            try:
                result = self.client.get_directions(
                    origin=origin,
                    destination=destination,
                    mode="driving"
                )
                
                if result:
                    # Update event with maps data
                    # We use setattr since these might be extra fields allowed by ConfigDict
                    event.duration_seconds = result.get("duration_seconds")
                    event.duration_text = result.get("duration_text")
                    event.distance_text = result.get("distance_text")
                    
                    # Also update description if travel_to is used
                    if event.travel_to and not event.description:
                        event.description = f"Drive from {origin} to {destination}"
                        
            except Exception:
                # Fail-fast is preferred, but for external APIs we might want 
                # to log and continue or raise depending on config.
                # For now, we'll let exceptions bubble up as per PipelineOrchestrator's design.
                raise
                
        return items

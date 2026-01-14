from typing import List, Optional
from itingen.core.base import BaseHydrator
from itingen.core.domain.events import Event
from itingen.integrations.maps.google_maps import GoogleMapsClient

class MapsHydrator(BaseHydrator[Event]):
    """Hydrator that enriches events with Google Maps data (duration, distance).
    
    AIDEV-NOTE: Uses GoogleMapsClient with local caching to minimize API calls 
    and ensure deterministic builds when keys are missing.
    """

    def __init__(self, api_key: Optional[str] = None, cache_dir: Optional[str] = None):
        """Initialize with Google Maps API key and optional cache directory.
        
        Args:
            api_key: Google Maps API key (defaults to GOOGLE_MAPS_API_KEY env var)
            cache_dir: Optional cache directory for route caching
        """
        self.client = GoogleMapsClient(api_key=api_key, cache_dir=cache_dir)

    def hydrate(self, items: List[Event], context=None) -> List[Event]:
        """Enrich drive events with duration and distance from Google Maps."""
        new_items = []
        for event in items:
            # Only hydrate drive events that don't have locked duration
            if event.kind != "drive" or getattr(event, "lock_duration", False):
                new_items.append(event)
                continue
            
            origin = event.travel_from
            destination = event.travel_to
            
            if not origin or not destination:
                # If travel fields are missing, try to use location
                # This is a bit brittle, but matches expected behavior for drives
                new_items.append(event)
                continue

            try:
                result = self.client.get_directions(
                    origin=origin,
                    destination=destination,
                    mode="driving"
                )
                
                if result:
                    updates = {
                        "duration_seconds": result.get("duration_seconds"),
                        "duration_text": result.get("duration_text"),
                        "distance_text": result.get("distance_text"),
                    }
                    
                    # Also update description if travel_to is used
                    if event.travel_to and not event.description:
                        updates["description"] = f"Drive from {origin} to {destination}"
                    
                    new_items.append(event.model_copy(update=updates))
                else:
                    new_items.append(event)
                        
            except Exception:
                # Fail-fast is preferred, but for external APIs we might want 
                # to log and continue or raise depending on config.
                # For now, we'll let exceptions bubble up as per PipelineOrchestrator's design.
                raise
                
        return new_items

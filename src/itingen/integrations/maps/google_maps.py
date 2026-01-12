import json
import hashlib
import os
from pathlib import Path
from typing import Optional, Dict, Any
import googlemaps
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, fallback to environment variables only

class GoogleMapsClient:
    """Client for Google Maps API with local caching."""

    def __init__(self, api_key: Optional[str] = None, cache_dir: Optional[str] = None):
        """Initialize with API key and optional cache directory.
        
        Args:
            api_key: Google Maps API key (defaults to GOOGLE_MAPS_API_KEY env var)
            cache_dir: Optional cache directory for route caching
        """
        self.api_key = api_key or os.environ.get("GOOGLE_MAPS_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_MAPS_API_KEY not found in environment or provided to client")
        
        self.client = googlemaps.Client(key=self.api_key)
        self.cache_dir = Path(cache_dir) if cache_dir else None
        if self.cache_dir:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_key(self, origin: str, destination: str, mode: str) -> str:
        """Generate a stable cache key for a route."""
        content = f"{origin}|{destination}|{mode}"
        return hashlib.sha256(content.encode()).hexdigest()

    def get_directions(self, origin: str, destination: str, mode: str = "driving") -> Optional[Dict[str, Any]]:
        """Get directions between two points, checking cache first."""
        cache_key = self._get_cache_key(origin, destination, mode)
        
        if self.cache_dir:
            cache_file = self.cache_dir / f"{cache_key}.json"
            if cache_file.exists():
                with open(cache_file, "r") as f:
                    return json.load(f)

        # Call Google Maps API
        try:
            result = self.client.directions(
                origin=origin,
                destination=destination,
                mode=mode
            )
            
            if not result:
                return None
                
            # Extract relevant info
            leg = result[0]["legs"][0]
            data = {
                "duration_seconds": leg["duration"]["value"],
                "duration_text": leg["duration"]["text"],
                "distance_text": leg["distance"]["text"],
                "origin": origin,
                "destination": destination,
                "mode": mode
            }
            
            # Save to cache
            if self.cache_dir:
                cache_file = self.cache_dir / f"{cache_key}.json"
                with open(cache_file, "w") as f:
                    json.dump(data, f)
                    
            return data
        except Exception:
            raise

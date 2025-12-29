import json
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any

class WeatherSparkClient:
    """Client for retrieving typical weather data with local caching."""

    def __init__(self, cache_dir: Optional[str] = None):
        """Initialize with optional cache directory."""
        self.cache_dir = Path(cache_dir) if cache_dir else None
        if self.cache_dir:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_key(self, location: str, date: str) -> str:
        """Generate a stable cache key for a location and date."""
        content = f"{location}|{date}"
        return hashlib.sha256(content.encode()).hexdigest()

    def get_typical_weather(self, location: str, date: str) -> Optional[Dict[str, Any]]:
        """Get typical weather for a location and date, checking cache first."""
        cache_key = self._get_cache_key(location, date)
        
        if self.cache_dir:
            cache_file = self.cache_dir / f"{cache_key}.json"
            if cache_file.exists():
                with open(cache_file, "r") as f:
                    return json.load(f)

        # In a real implementation, this would scrape or call an API.
        # For the generic version, we'll return None or a placeholder
        # if no cache is found, as we don't have the scrapers yet.
        # This matches the "Fail-Fast" principle.
        return None

"""WeatherSpark client for fetching typical weather data.

This module scrapes WeatherSpark.com to get historical climate data for specific
locations and dates. It includes aggressive caching to minimize requests.

Attribution: Include "Typical weather © WeatherSpark.com" near displayed data.
"""

import json
import hashlib
import re
import datetime as dt
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass

import requests


@dataclass(frozen=True)
class WeatherSparkPlace:
    """Represents a WeatherSpark location with its metadata."""
    key: str
    place_id: int
    city_label: str
    url_city_slug: str


# AIDEV-NOTE: Place map can be extended for new locations. Find place_id by
# visiting weatherspark.com and inspecting the URL structure.
PLACE_MAP: Dict[str, WeatherSparkPlace] = {
    "auckland": WeatherSparkPlace(
        key="auckland",
        place_id=144891,
        city_label="Auckland",
        url_city_slug="Auckland",
    ),
    "rotorua": WeatherSparkPlace(
        key="rotorua",
        place_id=144936,
        city_label="Rotorua",
        url_city_slug="Rotorua",
    ),
    "taupo": WeatherSparkPlace(
        key="taupo",
        place_id=144933,
        city_label="Taupo",
        url_city_slug="Taupo",
    ),
    "wellington": WeatherSparkPlace(
        key="wellington",
        place_id=144870,
        city_label="Wellington",
        url_city_slug="Wellington",
    ),
    "te_anau": WeatherSparkPlace(
        key="te_anau",
        place_id=144773,
        city_label="Te Anau",
        url_city_slug="Te-Anau",
    ),
    "queenstown": WeatherSparkPlace(
        key="queenstown",
        place_id=144792,
        city_label="Queenstown",
        url_city_slug="Queenstown",
    ),
    "waiheke": WeatherSparkPlace(
        key="waiheke",
        place_id=144891,
        city_label="Waiheke Island",
        url_city_slug="Auckland",
    ),
    "milford_sound": WeatherSparkPlace(
        key="milford_sound",
        place_id=144773,
        city_label="Milford Sound",
        url_city_slug="Te-Anau",
    ),
}


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

    def _infer_place_key(self, location_text: str) -> Optional[str]:
        """Infer place key from location text using pattern matching."""
        if not location_text:
            return None

        text = location_text.lower()

        # Check for known locations
        if any(k in text for k in ["waiheke", "oneroa", "onetangi", "matiatia"]):
            return "waiheke"
        if "milford sound" in text or "milford-sound" in text:
            return "milford_sound"
        if "queenstown" in text or "zqn" in text:
            return "queenstown"
        if "te anau" in text or "te-anau" in text:
            return "te_anau"
        if "wellington" in text:
            return "wellington"
        if "taupo" in text:
            return "taupo"
        if "rotorua" in text:
            return "rotorua"
        if "auckland" in text or "akl" in text:
            return "auckland"

        return None

    def _build_day_url(self, place: WeatherSparkPlace, date: dt.date) -> str:
        """Build WeatherSpark URL for a specific place and date."""
        month_name = date.strftime("%B")
        return (
            f"https://weatherspark.com/d/{place.place_id}/{date.month}/{date.day}/"
            f"Average-Weather-on-{month_name}-{date.day}-in-{place.url_city_slug}-New-Zealand"
        )

    def _html_to_text(self, html: str) -> str:
        """Convert HTML to plain text for parsing."""
        # Remove scripts and styles
        html = re.sub(r"<script[\s\S]*?</script>", " ", html, flags=re.IGNORECASE)
        html = re.sub(r"<style[\s\S]*?</style>", " ", html, flags=re.IGNORECASE)
        # Strip tags
        text = re.sub(r"<[^>]+>", " ", html)
        # Collapse whitespace
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def _parse_temp_range_f(self, text: str) -> Optional[tuple[int, int]]:
        """Parse temperature range from text."""
        # Match "typically ranges from XX°F to YY°F"
        m = re.search(r"typically ranges from\s+(\d+)\s*.F\s+to\s+(\d+)\s*.F", text)
        if not m:
            m = re.search(r"ranges from\s+(\d+)\s*.F\s+to\s+(\d+)\s*.F", text)
        if not m:
            return None

        lo = int(m.group(1))
        hi = int(m.group(2))
        return (lo, hi)

    def _parse_precip_chance_pct(self, text: str) -> Optional[int]:
        """Parse precipitation chance from text."""
        m = re.search(r"there is a\s+(\d+)%\s+chance", text, flags=re.IGNORECASE)
        if not m:
            return None
        return int(m.group(1))

    def _conditions_from_precip_fallback(self, precip_chance_pct: Optional[int]) -> Optional[str]:
        """Infer conditions from precipitation chance if direct parsing fails."""
        if isinstance(precip_chance_pct, int):
            if precip_chance_pct <= 15:
                return "mostly sunny"
            if precip_chance_pct <= 35:
                return "partly cloudy"
            if precip_chance_pct <= 55:
                return "mixed clouds"
            return "likely rain"
        return None

    def _parse_conditions(self, text: str, precip_chance_pct: Optional[int]) -> Optional[str]:
        """Parse sky conditions from text with fallback to precip-based inference."""
        # Try to find direct sky condition phrase
        m = re.search(
            r"\bthe sky is\s+(mostly clear|clear|partly cloudy|mostly cloudy|overcast)\b",
            text,
            flags=re.IGNORECASE,
        )
        if m:
            return m.group(1).strip().lower()

        # Alternative phrasing
        m2 = re.search(
            r"\b(typically|generally)\s+(mostly clear|clear|partly cloudy|mostly cloudy|overcast)\b",
            text,
            flags=re.IGNORECASE,
        )
        if m2:
            return m2.group(2).strip().lower()

        # Fallback to precip-based inference
        return self._conditions_from_precip_fallback(precip_chance_pct)

    def get_typical_weather(self, location: str, date: str) -> Optional[Dict[str, Any]]:
        """Get typical weather for a location and date, checking cache first.

        Args:
            location: Location string (e.g., "Auckland, New Zealand")
            date: Date string in YYYY-MM-DD format

        Returns:
            Dict with keys: high_temp_f, low_temp_f, conditions, precip_chance_pct
            or None if location is unknown or fetch fails.
        """
        cache_key = self._get_cache_key(location, date)

        # Check cache first
        if self.cache_dir:
            cache_file = self.cache_dir / f"{cache_key}.json"
            if cache_file.exists():
                with open(cache_file, "r") as f:
                    return json.load(f)

        # Infer place key from location
        place_key = self._infer_place_key(location)
        if not place_key:
            return None

        place = PLACE_MAP.get(place_key)
        if not place:
            return None

        # Parse date
        try:
            date_obj = dt.datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            return None

        # Build URL and fetch
        url = self._build_day_url(place, date_obj)

        try:
            resp = requests.get(
                url,
                timeout=20,
                headers={"User-Agent": "Mozilla/5.0 (itingen; +local script)"},
            )

            if resp.status_code != 200:
                return None

            text = self._html_to_text(resp.text)

            # Parse data
            temp_range_f = self._parse_temp_range_f(text)
            precip_chance_pct = self._parse_precip_chance_pct(text)
            conditions = self._parse_conditions(text, precip_chance_pct)

            if not temp_range_f:
                return None

            # Format output to match expected interface
            result = {
                "high_temp_f": temp_range_f[1],
                "low_temp_f": temp_range_f[0],
                "conditions": conditions,
                "precip_chance_pct": precip_chance_pct,
            }

            # Write to cache
            if self.cache_dir:
                cache_file = self.cache_dir / f"{cache_key}.json"
                with open(cache_file, "w") as f:
                    json.dump(result, f, indent=2)

            return result

        except Exception:
            return None

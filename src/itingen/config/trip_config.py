"""Trip configuration management.

AIDEV-NOTE: TripConfig loads and validates trip-specific configuration from
YAML files and provides access to trip directories and configuration data.
"""
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml


class TripConfig:
    """Load and manage trip-specific configuration.

    This class provides a centralized interface for accessing trip configuration
    data and directory paths. It loads configuration from a config.yaml file in
    the trip directory and provides type-safe accessors for common configuration
    values.

    Example:
        >>> config = TripConfig(trip_name="nz_2026")
        >>> events_dir = config.get_events_dir()
        >>> travelers = config.get_travelers()
    """

    def __init__(self, trip_name: str, trips_dir: Optional[Path] = None):
        """Initialize TripConfig.

        Args:
            trip_name: Name of the trip (directory name in trips/)
            trips_dir: Optional path to trips directory (defaults to ./trips)

        Raises:
            ValueError: If trip directory does not exist
            FileNotFoundError: If config.yaml is not found in trip directory
        """
        self.trip_name = trip_name
        self.trips_dir = (trips_dir or Path("trips")).resolve()
        self.trip_dir = (self.trips_dir / trip_name).resolve()

        if not self.trip_dir.exists():
            raise ValueError(f"Trip directory not found: {self.trip_dir}")

        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load config.yaml from trip directory.

        Returns:
            Dictionary containing configuration data

        Raises:
            FileNotFoundError: If config.yaml does not exist
        """
        config_path = self.trip_dir / "config.yaml"
        if not config_path.exists():
            raise FileNotFoundError(f"Trip config not found: {config_path}")

        with open(config_path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def get_events_dir(self) -> Path:
        """Get path to events directory.

        Returns:
            Path to the events directory
        """
        return self.trip_dir / "events"

    def get_venues_dir(self) -> Path:
        """Get path to venues directory.

        Returns:
            Path to the venues directory
        """
        return self.trip_dir / "venues"

    def get_prompts_dir(self) -> Path:
        """Get path to prompts directory.

        Returns:
            Path to the prompts directory
        """
        return self.trip_dir / "prompts"

    def get_travelers(self) -> List[Dict[str, str]]:
        """Get list of travelers from config.

        Returns:
            List of traveler dictionaries with 'name' and 'slug' keys.
            Returns empty list if 'people' key is not in config.
        """
        return self.config.get("people", [])

    def get_timezone(self) -> Optional[str]:
        """Get timezone from config.

        Returns:
            Timezone string (e.g., "America/Los_Angeles") or None if not set.
        """
        return self.config.get("timezone")

    def get_trip_name_from_config(self) -> Optional[str]:
        """Get trip name from config file.

        Returns:
            Trip name string from config or None if not set.

        Note:
            This is different from self.trip_name, which is the directory name.
            The config may contain a human-readable trip name.
        """
        return self.config.get("trip_name")

    def get(self, key: str, default: Any = None) -> Any:
        """Get arbitrary config value.

        Args:
            key: Config key to retrieve
            default: Default value if key doesn't exist

        Returns:
            Config value or default if key doesn't exist
        """
        return self.config.get(key, default)

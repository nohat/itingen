import yaml
import json
import glob
from pathlib import Path
from typing import Any, Dict, List, Optional
from itingen.core.base import BaseProvider
from itingen.core.domain.events import Event
from itingen.core.domain.venues import Venue
from itingen.utils.duration import parse_duration

class LocalFileProvider(BaseProvider[Event]):
    """Provider that loads trip data from the local filesystem."""

    def __init__(self, trip_dir: str | Path):
        self.trip_dir = Path(trip_dir)
        if not self.trip_dir.exists():
            raise ValueError(f"Trip directory not found: {self.trip_dir}")
        self.events_dir = self.trip_dir / "events"
        self.venues_dir = self.trip_dir / "venues"
        self.config_path = self.trip_dir / "config.yaml"

    def get_config(self) -> Dict[str, Any]:
        """Load and return trip-level configuration."""
        if not self.config_path.exists():
            return {}
        with open(self.config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def get_events(self) -> List[Event]:
        """Load and return trip events from Markdown files."""
        if not self.events_dir.exists():
            return []
        
        all_events = []
        # Find all .md files in the events directory
        day_files = sorted(glob.glob(str(self.events_dir / "*.md")))
        
        for day_file in day_files:
            all_events.extend(self._parse_markdown_file(day_file))
            
        return all_events

    def get_venues(self) -> Dict[str, Venue]:
        """Load and return venue information from JSON files."""
        venues = {}
        if not self.venues_dir.exists():
            return venues
            
        for venue_file in self.venues_dir.glob("*.json"):
            with open(venue_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                venue = Venue(**data)
                venues[venue.venue_id] = venue
                
        return venues

    def _parse_markdown_file(self, path: str) -> List[Event]:
        """Parse a single Markdown file for events."""
        events: List[Event] = []
        day_metadata: Dict[str, Any] = {}
        current_header: Optional[str] = None
        current_block: List[str] = []

        with open(path, "r", encoding="utf-8") as f:
            for raw in f:
                line = raw.rstrip("\n")

                # Parse day-level metadata (before first event)
                if current_header is None and line.startswith("- "):
                    body = line[2:]
                    if ":" in body:
                        k, v = body.split(":", 1)
                        day_metadata[k.strip()] = v.strip()
                    continue

                if line.startswith("### Event:"):
                    # Flush previous event block
                    if current_header is not None:
                        events.append(self._create_event(current_block, current_header, day_metadata))
                        current_block = []

                    current_header = line[len("### Event:") :].strip()
                    continue

                # Collect lines inside current event block
                if current_header is not None:
                    if line.startswith("## "):
                        if current_header is not None:
                            events.append(self._create_event(current_block, current_header, day_metadata))
                            current_block = []
                        current_header = None
                    else:
                        current_block.append(raw)

        # Flush final block
        if current_header is not None:
            events.append(self._create_event(current_block, current_header, day_metadata))

        return events

    def _create_event(self, lines: List[str], header: Optional[str], metadata: Dict[str, Any]) -> Event:
        """Create an Event object from a block of lines and metadata."""
        event_data = metadata.copy()
        if header:
            event_data["event_heading"] = header
            
        for raw in lines:
            line = raw.strip("\n")
            if not line.startswith("- "):
                continue
            body = line[2:]
            if ":" not in body:
                continue
            key, value = body.split(":", 1)
            key = key.strip()
            value = value.strip()
            
            # Simple normalization matching scaffold logic
            if key in {"who", "depends_on"}:
                event_data[key] = [p.strip() for p in value.split(",") if p.strip()]
            elif key in {"coordination_point", "hard_stop", "inferred"}:
                v = value.lower()
                event_data[key] = v in {"true", "yes", "y", "1"}
            elif key == "duration":
                # Parse duration string (e.g., "1h30m") into duration_seconds
                try:
                    event_data["duration_seconds"] = parse_duration(value)
                except ValueError as e:
                    # Fail fast on malformed duration
                    raise ValueError(f"Invalid duration in event '{header}': {e}") from e
            else:
                event_data[key] = value
                
        return Event(**event_data)

"""JSON emitter for itinerary data.

This module provides a JsonEmitter that outputs itinerary data in JSON format.
JSON output is useful for programmatic consumption and integration with other tools.
"""

import json
from typing import List
from pathlib import Path
from itingen.core.base import BaseEmitter
from itingen.core.domain.events import Event


class JsonEmitter(BaseEmitter[Event]):
    """Emitter that generates JSON representation of the itinerary.

    The JSON output includes all event fields and is suitable for:
    - API consumption
    - Data interchange with other systems
    - Programmatic analysis of trip data
    """

    def emit(self, itinerary: List[Event], output_path: str) -> str:
        """Write the itinerary to a JSON file.

        Args:
            itinerary: List of Event objects to serialize
            output_path: Path where the JSON file should be written

        Returns:
            The absolute path to the generated JSON file
        """
        path = Path(output_path)

        # Auto-add .json extension if not present
        if not path.suffix:
            path = path.with_suffix(".json")

        # Ensure parent directory exists
        path.parent.mkdir(parents=True, exist_ok=True)

        # Convert events to dictionaries using Pydantic's model_dump
        events_data = [event.model_dump(mode='json') for event in itinerary]

        # Create output structure
        output = {
            "events": events_data
        }

        # Write JSON to file with pretty printing
        with open(path, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

        return str(path)

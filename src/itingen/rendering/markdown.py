from typing import List
from pathlib import Path
from itingen.core.base import BaseEmitter
from itingen.core.domain.events import Event

class MarkdownEmitter(BaseEmitter[Event]):
    """Emitter that generates a Markdown representation of the itinerary."""

    def emit(self, itinerary: List[Event], output_path: str) -> bool:
        """Write the itinerary to a Markdown file."""
        try:
            path = Path(output_path)
            if not path.suffix:
                path = path.with_suffix(".md")
            
            path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, "w", encoding="utf-8") as f:
                f.write("# Trip Itinerary\n\n")
                
                for event in itinerary:
                    heading = event.event_heading or "Untitled Event"
                    f.write(f"## {heading}\n")
                    
                    if event.kind:
                        f.write(f"- **Kind**: {event.kind}\n")
                    if event.location:
                        f.write(f"- **Location**: {event.location}\n")
                    if hasattr(event, "duration_text") and event.duration_text:
                        f.write(f"- **Duration**: {event.duration_text}\n")
                    if hasattr(event, "distance_text") and event.distance_text:
                        f.write(f"- **Distance**: {event.distance_text}\n")
                    if event.time_utc:
                        f.write(f"- **Time (UTC)**: {event.time_utc}\n")
                    if event.who:
                        f.write(f"- **Who**: {', '.join(event.who)}\n")
                    
                    if event.description:
                        f.write(f"\n{event.description}\n")
                    
                    if event.travel_to:
                        f.write(f"\n### Travel To\n{event.travel_to}\n")
                    
                    f.write("\n---\n\n")
            
            return True
        except Exception:
            return False

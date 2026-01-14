import datetime
from typing import List
from pathlib import Path
from itingen.core.base import BaseEmitter
from itingen.core.domain.events import Event
from itingen.utils.duration import format_duration
from itingen.utils.grouping import group_events_by_date

class MarkdownEmitter(BaseEmitter[Event]):
    """Emitter that generates a Markdown representation of the itinerary."""

    def emit(self, itinerary: List[Event], output_path: str) -> str:
        """Write the itinerary to a Markdown file."""
        path = Path(output_path)
        if not path.suffix:
            path = path.with_suffix(".md")
        
        path.parent.mkdir(parents=True, exist_ok=True)

        events_by_date = group_events_by_date(itinerary)

        with open(path, "w", encoding="utf-8") as f:
            f.write("# Trip Itinerary\n\n")
            
            sorted_dates = sorted(events_by_date.keys())
            last_sleep_location = None
            
            for date_str in sorted_dates:
                # Add Day Header
                try:
                    dt = datetime.datetime.strptime(date_str, "%Y-%m-%d")
                    day_header = dt.strftime("%Y-%m-%d (%A)")
                except ValueError:
                    day_header = date_str
                
                f.write(f"## {day_header}\n\n")
                
                day_events = events_by_date[date_str]
                
                # Wake up marker
                wake_loc = last_sleep_location
                first_event = day_events[0] if day_events else None
                if not wake_loc and first_event:
                    # Inferred from first event location or travel_from
                    wake_loc = first_event.location or first_event.travel_from or "your current location"
                
                if wake_loc:
                    f.write(f"- **Wake up – {wake_loc}.**\n")
                    # In original script, it adds a "must be ready for" line if the first event has a time
                    if first_event and (first_event.time_local or first_event.no_later_than):
                        target_time = first_event.time_local or first_event.no_later_than
                        if " " in target_time:
                            target_time = target_time.split(" ")[1]
                        f.write(f"  - Between now and {target_time}, you have flexible time but must be ready for {first_event.event_heading or first_event.description or 'your first event'}.\n")
                    f.write("\n")
                
                for event in day_events:
                    heading = event.event_heading or "Untitled Event"
                    
                    # Time string
                    time_str = "TBD"
                    if event.time_local:
                        try:
                            # Assuming time_local is HH:MM or YYYY-MM-DD HH:MM
                            if " " in event.time_local:
                                time_str = event.time_local.split(" ")[1]
                            else:
                                time_str = event.time_local
                        except Exception:
                            time_str = event.time_local
                    
                    # Participants
                    with_str = ""
                    if event.who:
                        with_str = f" (with {', '.join(event.who)})"
                    
                    # Duration (format duration_seconds to display)
                    dur_str = ""
                    duration_seconds = getattr(event, "duration_seconds", None)
                    if duration_seconds is not None:
                        formatted = format_duration(duration_seconds)
                        if formatted:
                            dur_str = f" ({formatted})"
                    
                    # Main event line
                    f.write(f"- **{time_str} – {heading}{with_str}.**")
                    if event.description:
                        f.write(f" {event.description}")
                    if dur_str:
                        f.write(f" {dur_str}")
                    f.write("\n")

                    # Image reference (if available and file exists), rendered as standalone element
                    image_path = getattr(event, "image_path", None)
                    if image_path and Path(image_path).exists():
                        f.write(f"![{heading}]({image_path})\n\n")

                    # Detail bullets
                    if event.who:
                        f.write(f"  - With: {', '.join(event.who)}\n")
                    
                    if getattr(event, "meal", None):
                        f.write(f"  - Meal: {event.meal}.\n")
                    
                    be_ready = getattr(event, "be_ready", None)
                    if be_ready:
                        f.write(f"  - {be_ready}\n")
                    
                    # Times line
                    # In scaffold: "  - Times: 09:00–09:30."
                    # For now, just showing the start time if available
                    if time_str != "TBD":
                         # We'd need end time logic here
                         f.write(f"  - Times: {time_str}–TBD.\n")
                    
                    if event.emotional_triggers:
                        f.write(f"  - Emotional triggers / frustrations: {event.emotional_triggers}.\n")
                    if event.emotional_high_point:
                        f.write(f"  - Emotional high point: {event.emotional_high_point}.\n")
                    
                    # Transition
                    trans = event.transition_from_prev
                    if trans:
                        f.write(f"  - Transition logistics: {trans}\n")
                    elif event.travel_to:
                        # Fallback to simple travel_to if no descriptive transition
                        f.write(f"  - Transition logistics: Travel to {event.travel_to}\n")

                    if event.coordination_point:
                        f.write("  - This is a coordination point where people need to be together.\n")
                    
                    if getattr(event, "notes", None):
                        f.write(f"  - Notes: {event.notes}\n")

                    # Wrap up timing
                    wrap_up = getattr(event, "wrap_up_time", None)
                    next_title = getattr(event, "next_event_title", None)
                    if wrap_up and next_title:
                         f.write(f"  - Plan to wrap this up by {wrap_up} so you're ready for {next_title}.\n")
                    
                    f.write("\n")
                    
                    # Track sleep location for next day
                    kind = (event.kind or "").strip().lower()
                    if kind in {"lodging_checkin", "lodging_stay"}:
                        last_sleep_location = event.location
                    elif kind == "flight_departure":
                         # Check for overnight flight
                         if event.duration and "h" in event.duration:
                             try:
                                 hours = int(event.duration.split("h")[0])
                                 if hours >= 6:
                                     last_sleep_location = f"on the plane ({event.travel_from} -> {event.travel_to})"
                             except ValueError:
                                 pass

                # Sleep marker
                sleep_loc = last_sleep_location or "your current location"
                f.write(f"- **Go to sleep at {sleep_loc}.**\n\n")
                f.write("---\n\n")
        
        return str(path)

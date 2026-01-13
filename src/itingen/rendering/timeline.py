from typing import List, Dict, Optional
import datetime
from dataclasses import dataclass
from itingen.core.domain.events import Event

@dataclass
class TimelineDay:
    date_str: str
    day_header: str
    events: List[Event]
    wake_up_location: Optional[str] = None
    first_event_target_time: Optional[str] = None
    first_event_title: Optional[str] = None
    sleep_location: Optional[str] = None
    banner_image_path: Optional[str] = None  # Future proofing for day banners
    weather_high: Optional[float] = None
    weather_low: Optional[float] = None
    weather_conditions: Optional[str] = None

class TimelineProcessor:
    """Process raw events into a structured timeline with days and markers."""

    def process(self, itinerary: List[Event]) -> List[TimelineDay]:
        events_by_date: Dict[str, List[Event]] = {}
        
        # 1. Group by date
        for event in itinerary:
            date_str = getattr(event, "date", None)
            if not date_str and event.time_utc:
                try:
                    dt = datetime.datetime.fromisoformat(event.time_utc.replace('Z', '+00:00'))
                    date_str = dt.strftime("%Y-%m-%d")
                except ValueError:
                    date_str = "TBD"
            elif not date_str:
                date_str = "TBD"
            
            if date_str not in events_by_date:
                events_by_date[date_str] = []
            events_by_date[date_str].append(event)

        sorted_dates = sorted(events_by_date.keys())
        timeline_days: List[TimelineDay] = []
        last_sleep_location = None

        for date_str in sorted_dates:
            day_events = events_by_date[date_str]
            
            # Format header
            try:
                dt = datetime.datetime.strptime(date_str, "%Y-%m-%d")
                day_header = dt.strftime("%Y-%m-%d (%A)")
            except ValueError:
                day_header = date_str

            # Determine Wake Up Location
            wake_loc = last_sleep_location
            first_event = day_events[0] if day_events else None
            
            if not wake_loc and first_event:
                wake_loc = first_event.location or first_event.travel_from or "your current location"

            # Determine First Event Target Time
            target_time = None
            first_title = None
            if first_event and (first_event.time_local or first_event.no_later_than):
                target_time = first_event.time_local or first_event.no_later_than
                if target_time and " " in target_time:
                    target_time = target_time.split(" ")[1]
                first_title = first_event.event_heading or first_event.description or 'your first event'

            # Determine Sleep Location for THIS day (to be used next day or printed at end)
            current_sleep_loc = None
            for event in day_events:
                kind = (event.kind or "").strip().lower()
                if kind in {"lodging_checkin", "lodging_stay"}:
                    current_sleep_loc = event.location
                elif kind == "flight_departure":
                    if getattr(event, "duration", None) and "h" in str(event.duration):
                        try:
                            hours = int(str(event.duration).split("h")[0])
                            if hours >= 6:
                                current_sleep_loc = f"on the plane ({event.travel_from} -> {event.travel_to})"
                        except ValueError:
                            pass
            
            # Carry over sleep location if not changed
            if not current_sleep_loc and last_sleep_location:
                current_sleep_loc = last_sleep_location # Default to staying same place? 
                # Actually, scaffold logic implies if not set, we default to "current location" 
                # but for tracking *across* days, we usually want to know where we ended up.
                # In `markdown.py`:
                # if kind in checkin/stay: last_sleep = loc
                # elif long flight: last_sleep = plane
                # else: last_sleep remains what it was (implicitly)
                pass 
            
            # If we found a specific sleep location for this day, update the tracker
            if current_sleep_loc:
                last_sleep_location = current_sleep_loc
            
            # The display string for "Go to sleep at..."
            display_sleep_loc = last_sleep_location or "your current location"

            # Aggregate weather data (take first available from events)
            weather_high = None
            weather_low = None
            weather_conditions = None
            for event in day_events:
                # WeatherHydrator uses event.weather_temp_high/low/conditions
                # We check for these fields on the Event model
                if getattr(event, "weather_temp_high", None) is not None:
                    weather_high = event.weather_temp_high
                    weather_low = getattr(event, "weather_temp_low", None)
                    weather_conditions = getattr(event, "weather_conditions", None)
                    break

            timeline_days.append(TimelineDay(
                date_str=date_str,
                day_header=day_header,
                events=day_events,
                wake_up_location=wake_loc,
                first_event_target_time=target_time,
                first_event_title=first_title,
                sleep_location=display_sleep_loc,
                weather_high=weather_high,
                weather_low=weather_low,
                weather_conditions=weather_conditions
            ))

        return timeline_days

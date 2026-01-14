"""Hydrator for adding emotional annotations to events.

AIDEV-NOTE: This hydrator adds 'emotional_triggers' and 'emotional_high_point' 
to events based on their kind and metadata, following the patterns from 
the original NZ trip system.
"""

from typing import List, Tuple, TypeVar
from itingen.core.base import BaseHydrator
from itingen.core.domain.events import Event

T = TypeVar('T')

class EmotionalAnnotationHydrator(BaseHydrator[Event]):
    """Adds emotional annotations to stress-heavy event types."""

    def hydrate(self, items: List[T], context=None) -> List[T]:
        """Enrich events with emotional metadata."""
        new_items = []
        for event in items:
            kind = (event.kind or "").strip().lower()
            travel_mode = (getattr(event, "travel_mode", None) or "").strip().lower()
            heading = (event.event_heading or "").lower()
            
            # Stressy kinds from original script
            stressy_kinds = {
                "flight_departure",
                "flight_arrival",
                "airport_buffer",
                "drive",
                "ferry",
                "lodging_checkin",
                "lodging_checkout",
                "decision",
            }
            
            # Skip short drives (< 20m) if duration is available
            is_stressy = kind in stressy_kinds
            if kind == "drive" and hasattr(event, "duration"):
                # Simple duration check if possible
                pass # For now, keep it simple

            if is_stressy:
                triggers, high_point = self._get_annotations(kind, travel_mode, heading)
                updates = {
                    "emotional_triggers": triggers,
                    "emotional_high_point": high_point
                }
                new_items.append(event.model_copy(update=updates))
            else:
                new_items.append(event)

        return new_items

    def _get_annotations(self, kind: str, travel_mode: str, heading: str) -> Tuple[str, str]:
        """Logic extracted from the original NZ trip system."""
        if kind in {"flight_departure", "airport_buffer"}:
            return (
                "airport crowds, lines, noise, bright lights, security uncertainty, "
                "fear of being late or missing the flight",
                "the moment you are through security and settled at the gate or in your seat, "
                "knowing the logistics are handled"
            )
        elif kind == "flight_arrival":
            return (
                "jet lag, long waits at immigration and baggage claim, feeling disoriented "
                "in a new airport",
                "stepping into the arrivals area and realizing you have actually arrived"
            )
        elif travel_mode == "uber":
            return (
                "traffic, surge pricing, waiting for the car to arrive, bathroom timing, "
                "worrying about getting stuck in traffic or cutting it close",
                "settling into the ride knowing someone else is driving and that the trip "
                "is now genuinely underway"
            )
        elif kind == "drive" or travel_mode == "driving":
            return (
                "traffic, winding roads, motion sickness, bathroom timing, "
                "worrying about arriving late or getting lost",
                "settling into the drive with scenery/music/conversation and feeling the trip "
                "moving forward"
            )
        elif kind == "ferry":
            return (
                "crowds during boarding, motion sickness, wind/cold, limited seating choices",
                "standing on deck with views of the water and coastline"
            )
        elif kind.startswith("lodging_"):
            if "check" in kind or "check" in heading:
                return (
                    "front-desk logistics, room readiness, decisions about beds and unpacking",
                    "first moment in the room when you can drop bags and exhale"
                )
            else:
                return (
                    "noise levels, sharing space, coordinating bedtimes and downtime with others",
                    "having a safe base where you can fully decompress and reset"
                )
        elif kind == "decision":
            return (
                "decision paralysis, FOMO, balancing your needs with the group’s preferences",
                "clarity and relief once a decision is actually made"
            )
        else:
            return (
                "being late, unclear instructions, performance pressure, sensory overload, "
                "worrying about whether you will enjoy it",
                "the immersed moment when the activity is underway and you can just be present "
                "and curious"
            )

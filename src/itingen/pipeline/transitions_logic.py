"""Hydrator for generating transition descriptions between events.

AIDEV-NOTE: This hydrator uses a registry of transition patterns to describe 
how to move from one event to the next, following the logic from the 
original NZ trip system.
"""

from typing import List, Optional
from itingen.core.base import BaseHydrator
from itingen.core.domain.events import Event


class TransitionHydrator(BaseHydrator[Event]):
    """Enriches events with descriptive transition logistics from the previous event."""

    def hydrate(self, items: List[Event]) -> List[Event]:
        """Add transition descriptions to events based on their predecessor."""
        if not items:
            return []

        new_items = []
        prev_ev: Optional[Event] = None
        for ev in items:
            updates = {}
            if prev_ev is not None:
                # Only calculate if not already set (e.g. from source)
                if not ev.transition_from_prev:
                    transition = self._describe_transition(prev_ev, ev)
                    if transition:
                        updates["transition_from_prev"] = transition
            
            if updates:
                new_items.append(ev.model_copy(update=updates))
            else:
                new_items.append(ev)
                
            prev_ev = ev

        return new_items

    def _describe_transition(self, prev_ev: Event, ev: Event) -> Optional[str]:
        """Logic extracted from the original NZ trip system's describe_transition_logistics."""
        prev_kind = (prev_ev.kind or "").strip().lower()
        kind = (ev.kind or "").strip().lower()

        prev_mode = getattr(prev_ev, "travel_mode", "").strip().lower()

        prev_loc = (prev_ev.location or prev_ev.travel_to or "").strip()
        loc = (ev.location or ev.travel_from or ev.travel_to or "").strip()

        # Helper to append driver/parking (simplified for now)
        def _with_extras(text: str) -> str:
            driver = getattr(ev, "driver", "").strip()
            parking = getattr(ev, "parking", "").strip()
            extras = []
            if driver:
                extras.append(f"{driver} will be driving")
            if parking:
                extras.append(f"plan to park {parking}")
            
            if not extras:
                return text
            
            base = text.rstrip()
            if base.endswith("."):
                base = base[:-1]
            return base + ". " + "; ".join(extras) + "."

        # Drive/ride into an airport buffer
        if prev_kind == "drive" and kind == "airport_buffer":
            if prev_mode == "uber":
                return _with_extras(f"Arrive by car at {loc or 'the airport'}, unload luggage, and move together into the check-in area.")
            return _with_extras(f"Park or arrive at {loc or 'the airport'}, secure the car, and bring everyone with their luggage into the terminal.")

        # Airport buffer into a flight departure
        if prev_kind == "airport_buffer" and kind == "flight_departure":
            return _with_extras(f"From the waiting area at {prev_loc or 'the airport'}, move to the correct gate, complete any final boarding checks, and board together when called.")

        # Flight arrival into an arrivals or airport buffer
        if prev_kind == "flight_arrival" and kind in {"arrivals_buffer", "airport_buffer"}:
            return _with_extras(f"Walk from the plane to immigration and baggage claim, clear formalities, then regroup in {loc or 'the arrivals hall'}.")

        # Arrivals/buffer into city transfer
        if prev_kind in {"arrivals_buffer", "airport_buffer"} and kind in {"ferry", "drive"}:
            origin = prev_loc or "the airport arrivals hall"
            dest = loc or "your next departure point"
            if "akl airport" in dest.lower() and "ferry terminal" in dest.lower():
                 return _with_extras("After clearing arrivals at AKL, move together into the public arrivals hall, follow signs to ground transport (taxis, rideshares, or shuttles), ride into central Auckland, and get dropped at Auckland Ferry Terminal in time for the ferry.")
            return _with_extras(f"After clearing the airport, move from {origin} to ground transport and travel to {dest}, allowing a buffer for traffic and wayfinding before your next departure.")

        # Ferry segment
        if kind == "ferry":
            origin = (getattr(ev, "travel_from", "") or prev_loc or "the ferry terminal").strip()
            dest = (getattr(ev, "travel_to", "") or loc or "your destination").strip()
            return _with_extras(f"Make your way to {origin}, board the ferry together, and take the boat ride across to {dest}.")

        # Ferry into lodging check-in
        if prev_kind == "ferry" and kind == "lodging_checkin":
            return _with_extras(f"Disembark the ferry, make your way to {loc or 'the lodging'}, and bring bags to reception for check-in.")

        # Short city drive into lodging
        if prev_kind == "drive" and kind == "lodging_checkin":
            return _with_extras(f"Arrive at {loc or 'your lodging'}, unload bags, and head to reception/check-in.")

        # Lodging checkout into airport buffer or next drive
        if prev_kind == "lodging_checkout" and kind in {"airport_buffer", "drive"}:
            return _with_extras(f"After checkout, move from {prev_loc or 'the hotel'} to {loc or 'your next departure point'}, keeping bags with you and allowing time for any transport or traffic.")

        # Ferry arrival into a follow-on drive
        if prev_kind == "ferry" and kind == "drive":
            drive_to = (getattr(ev, "travel_to", "") or "your next destination").strip()
            return _with_extras(f"Disembark from the ferry, walk with the group to the car pickup area, meet your car, load bags, and start the drive to {drive_to}.")

        # Generic fallback
        if prev_loc and loc:
            return f"Move from {prev_loc} to {loc}."

        return None

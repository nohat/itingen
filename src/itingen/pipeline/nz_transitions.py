"""NZ-specific transition patterns for the TransitionRegistry.

This module contains the hardcoded transition logic extracted from the original
NZ trip system. These patterns describe how to move between different event types.
"""

from typing import Optional
from itingen.core.domain.events import Event
from itingen.pipeline.transitions import TransitionRegistry


def _with_extras(text: str, event: Event) -> str:
    """Append driver and parking information to transition text.

    Args:
        text: Base transition description.
        event: Current event that may have driver/parking info.

    Returns:
        Enhanced transition text with driver/parking details.
    """
    driver = getattr(event, "driver", "").strip()
    parking = getattr(event, "parking", "").strip()
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


def create_nz_transition_registry() -> TransitionRegistry:
    """Create a TransitionRegistry with NZ-specific transition patterns.

    Returns:
        A TransitionRegistry populated with NZ trip transition handlers.
    """
    registry = TransitionRegistry()

    # Drive/ride into an airport buffer
    def drive_to_airport_buffer(prev: Event, curr: Event) -> str:
        prev_mode = getattr(prev, "travel_mode", "").strip().lower()
        loc = (curr.location or "the airport").strip()

        if prev_mode == "uber":
            return _with_extras(
                f"Arrive by car at {loc}, unload luggage, and move together into the check-in area.",
                curr
            )
        return _with_extras(
            f"Park or arrive at {loc}, secure the car, and bring everyone with their luggage into the terminal.",
            curr
        )

    registry.register("drive", "airport_buffer", drive_to_airport_buffer)

    # Airport buffer into a flight departure
    def airport_buffer_to_flight(prev: Event, curr: Event) -> str:
        prev_loc = (prev.location or "the airport").strip()
        return _with_extras(
            f"From the waiting area at {prev_loc}, move to the correct gate, complete any final boarding checks, and board together when called.",
            curr
        )

    registry.register("airport_buffer", "flight_departure", airport_buffer_to_flight)

    # Flight arrival into an arrivals or airport buffer
    def flight_to_arrivals(prev: Event, curr: Event) -> str:
        loc = (curr.location or "the arrivals hall").strip()
        return _with_extras(
            f"Walk from the plane to immigration and baggage claim, clear formalities, then regroup in {loc}.",
            curr
        )

    registry.register("flight_arrival", "arrivals_buffer", flight_to_arrivals)
    registry.register("flight_arrival", "airport_buffer", flight_to_arrivals)

    # Arrivals/buffer into city transfer (ferry or drive)
    def arrivals_to_transport(prev: Event, curr: Event) -> str:
        origin = (prev.location or "the airport arrivals hall").strip()
        dest = (curr.location or "your next departure point").strip()

        # Special case for AKL airport to ferry terminal
        if "akl airport" in dest.lower() and "ferry terminal" in dest.lower():
            return _with_extras(
                "After clearing arrivals at AKL, move together into the public arrivals hall, follow signs to ground transport (taxis, rideshares, or shuttles), ride into central Auckland, and get dropped at Auckland Ferry Terminal in time for the ferry.",
                curr
            )

        return _with_extras(
            f"After clearing the airport, move from {origin} to ground transport and travel to {dest}, allowing a buffer for traffic and wayfinding before your next departure.",
            curr
        )

    registry.register("arrivals_buffer", "ferry", arrivals_to_transport)
    registry.register("arrivals_buffer", "drive", arrivals_to_transport)
    registry.register("airport_buffer", "ferry", arrivals_to_transport)
    registry.register("airport_buffer", "drive", arrivals_to_transport)

    # Ferry segment - matches ANY transition to a ferry
    # This is a wildcard pattern that was in the original NZ trip code
    def ferry_segment(prev: Event, curr: Event) -> str:
        prev_loc = (prev.location or "the ferry terminal").strip()
        origin = (getattr(curr, "travel_from", "") or prev_loc or "the ferry terminal").strip()
        dest = (getattr(curr, "travel_to", "") or curr.location or "your destination").strip()

        return _with_extras(
            f"Make your way to {origin}, board the ferry together, and take the boat ride across to {dest}.",
            curr
        )

    # Register with wildcard "*" to match any transition TO a ferry
    # This must be registered AFTER more specific patterns (like arrivals_buffer->ferry)
    # so that specific patterns match first
    registry.register("*", "ferry", ferry_segment)

    # Ferry into lodging check-in
    def ferry_to_lodging(prev: Event, curr: Event) -> str:
        loc = (curr.location or "the lodging").strip()
        return _with_extras(
            f"Disembark the ferry, make your way to {loc}, and bring bags to reception for check-in.",
            curr
        )

    registry.register("ferry", "lodging_checkin", ferry_to_lodging)

    # Short city drive into lodging
    def drive_to_lodging(prev: Event, curr: Event) -> str:
        loc = (curr.location or "your lodging").strip()
        return _with_extras(
            f"Arrive at {loc}, unload bags, and head to reception/check-in.",
            curr
        )

    registry.register("drive", "lodging_checkin", drive_to_lodging)

    # Lodging checkout into airport buffer or next drive
    def lodging_checkout_to_transport(prev: Event, curr: Event) -> str:
        prev_loc = (prev.location or "the hotel").strip()
        loc = (curr.location or "your next departure point").strip()
        return _with_extras(
            f"After checkout, move from {prev_loc} to {loc}, keeping bags with you and allowing time for any transport or traffic.",
            curr
        )

    registry.register("lodging_checkout", "airport_buffer", lodging_checkout_to_transport)
    registry.register("lodging_checkout", "drive", lodging_checkout_to_transport)

    # Ferry arrival into a follow-on drive
    def ferry_to_drive(prev: Event, curr: Event) -> str:
        drive_to = (getattr(curr, "travel_to", "") or "your next destination").strip()
        return _with_extras(
            f"Disembark from the ferry, walk with the group to the car pickup area, meet your car, load bags, and start the drive to {drive_to}.",
            curr
        )

    registry.register("ferry", "drive", ferry_to_drive)

    # Generic fallback for any transition with locations
    # This is registered last so specific patterns match first
    def generic_fallback(prev: Event, curr: Event) -> Optional[str]:
        prev_loc = (prev.location or prev.travel_to or "").strip()
        curr_loc = (curr.location or curr.travel_from or curr.travel_to or "").strip()

        if prev_loc and curr_loc:
            return f"Move from {prev_loc} to {curr_loc}."
        return None

    # Note: Generic fallback is intentionally NOT registered to the registry
    # It's handled by TransitionHydrator as a final fallback

    return registry

"""Database-backed provider for trip data."""

from typing import Any, Dict, List

from itingen.core.base import BaseProvider
from itingen.core.domain.events import Event
from itingen.core.domain.venues import Venue
from itingen.db.connection import get_connection
from itingen.db.repository import (
    EventRepository,
    TravelerRepository,
    TripRepository,
    VenueRepository,
)


class DatabaseProvider(BaseProvider[Event]):
    """Provider that loads trip data from the SQLite database."""

    def __init__(self, db_path: str, trip_id: str):
        self.db_path = db_path
        self.trip_id = trip_id

    def get_events(self) -> List[Event]:
        conn = get_connection(self.db_path)
        try:
            return EventRepository.get_events_for_trip(conn, self.trip_id)
        finally:
            conn.close()

    def get_venues(self) -> Dict[str, Venue]:
        conn = get_connection(self.db_path)
        try:
            return VenueRepository.get_venues_for_trip(conn, self.trip_id)
        finally:
            conn.close()

    def get_config(self) -> Dict[str, Any]:
        conn = get_connection(self.db_path)
        try:
            trip = TripRepository.get_trip(conn, self.trip_id)
            if trip is None:
                raise ValueError(f"Trip '{self.trip_id}' not found in database")

            travelers = TravelerRepository.get_travelers_for_trip(conn, self.trip_id)

            return {
                "trip_name": trip["trip_name"],
                "timezone": trip["timezone"],
                "people": [
                    {"name": t["name"], "slug": t["slug"]}
                    for t in travelers
                ],
            }
        finally:
            conn.close()

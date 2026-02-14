"""Migration script: file-based trips → SQLite database."""

import uuid
from pathlib import Path
from typing import List

from itingen.core.domain.events import Event
from itingen.db.connection import get_connection, transaction
from itingen.db.repository import (
    EventRepository,
    TravelerRepository,
    TripRepository,
    VenueRepository,
)
from itingen.providers.file_provider import LocalFileProvider


class MigrationError(Exception):
    """Raised when migration fails."""


def migrate_trip(trip_dir: Path, db_path: str) -> str:
    """Migrate a trip from file-based storage to the database.

    Returns the trip_id.
    Raises MigrationError on validation failures or duplicate trips.
    """
    if not trip_dir.exists():
        raise MigrationError(f"Trip directory not found: {trip_dir}")

    # Load data via existing provider
    provider = LocalFileProvider(trip_dir)
    config = provider.get_config()

    if not config:
        raise MigrationError(f"Missing or empty config.yaml in {trip_dir}")

    trip_name = config.get("trip_name")
    timezone = config.get("timezone")
    people = config.get("people", [])

    if not trip_name:
        raise MigrationError(f"config.yaml missing 'trip_name' in {trip_dir}")
    if not timezone:
        raise MigrationError(f"config.yaml missing 'timezone' in {trip_dir}")

    trip_id = trip_dir.name

    # Load events and venues
    events = provider.get_events()
    venues = provider.get_venues()

    # Infer trip dates from events
    start_date, end_date = _infer_trip_dates(config, events)

    conn = get_connection(db_path)
    try:
        # Check for duplicate trip
        existing = TripRepository.get_trip(conn, trip_id)
        if existing:
            raise MigrationError(f"Trip '{trip_id}' already exists in database")

        with transaction(conn):
            # Insert trip
            TripRepository.insert_trip(
                conn,
                trip_id=trip_id,
                trip_name=trip_name,
                start_date=start_date,
                end_date=end_date,
                timezone=timezone,
            )

            # Insert travelers
            for person in people:
                name = person.get("name")
                slug = person.get("slug")
                if not name or not slug:
                    raise MigrationError(f"Person missing name or slug: {person}")
                TravelerRepository.insert_traveler(
                    conn, trip_id, str(uuid.uuid4()), name, slug
                )

            # Insert venues
            for venue in venues.values():
                VenueRepository.insert_venue(conn, trip_id, venue)

            # Insert events
            for event in events:
                EventRepository.insert_event(conn, trip_id, event)

    finally:
        conn.close()

    return trip_id


def _infer_trip_dates(config: dict, events: List[Event]) -> tuple:
    """Get trip dates from config or infer from events."""
    # Check config for explicit dates
    start = config.get("start_date")
    end = config.get("end_date")
    if start and end:
        return str(start), str(end)

    # Check nested dates
    dates = config.get("dates", {})
    if isinstance(dates, dict):
        start = dates.get("start")
        end = dates.get("end")
        if start and end:
            return str(start), str(end)

    # Infer from event time_local fields
    time_values = []
    for e in events:
        if e.time_local:
            time_values.append(e.time_local)
        elif e.time_utc:
            time_values.append(e.time_utc)

    if not time_values:
        raise MigrationError(
            "Cannot infer trip dates: no events have time_local or time_utc. "
            "Please add 'start_date' and 'end_date' to config.yaml"
        )

    # Extract date portion (first 10 chars of ISO datetime)
    dates_only = sorted(t[:10] for t in time_values)
    return dates_only[0], dates_only[-1]

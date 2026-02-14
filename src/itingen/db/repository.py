"""Database repositories for itingen domain models."""

import json
import sqlite3
import uuid
from typing import Any, Dict, List, Optional

from itingen.core.domain.events import Event
from itingen.core.domain.venues import (
    Venue,
    VenueAddress,
    VenueBooking,
    VenueContact,
    VenueMetadata,
)


def _new_uuid() -> str:
    return str(uuid.uuid4())


class TripRepository:
    @staticmethod
    def insert_trip(
        conn: sqlite3.Connection,
        trip_id: str,
        trip_name: str,
        start_date: str,
        end_date: str,
        timezone: str,
        theme_config: Optional[str] = None,
        extra_config: Optional[str] = None,
    ) -> str:
        conn.execute(
            "INSERT INTO trips (id, trip_name, start_date, end_date, timezone, theme_config, extra_config) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (trip_id, trip_name, start_date, end_date, timezone, theme_config, extra_config),
        )
        return trip_id

    @staticmethod
    def get_trip(conn: sqlite3.Connection, trip_id: str) -> Optional[sqlite3.Row]:
        return conn.execute("SELECT * FROM trips WHERE id = ?", (trip_id,)).fetchone()


class TravelerRepository:
    @staticmethod
    def insert_traveler(
        conn: sqlite3.Connection,
        trip_id: str,
        traveler_id: str,
        name: str,
        slug: str,
    ) -> str:
        conn.execute(
            "INSERT INTO travelers (id, trip_id, name, slug) VALUES (?, ?, ?, ?)",
            (traveler_id, trip_id, name, slug),
        )
        return traveler_id

    @staticmethod
    def get_travelers_for_trip(conn: sqlite3.Connection, trip_id: str) -> List[sqlite3.Row]:
        return conn.execute(
            "SELECT * FROM travelers WHERE trip_id = ? ORDER BY name", (trip_id,)
        ).fetchall()


class VenueRepository:
    @staticmethod
    def insert_venue(conn: sqlite3.Connection, trip_id: str, venue: Venue) -> str:
        row_id = _new_uuid()

        # Flatten address
        address_street = address_city = address_region = address_country = address_postcode = None
        address_raw = None
        if isinstance(venue.address, VenueAddress):
            address_street = venue.address.street
            address_city = venue.address.city
            address_region = venue.address.region
            address_country = venue.address.country
            address_postcode = venue.address.postcode
        elif isinstance(venue.address, str):
            address_raw = venue.address

        # Flatten contact
        contact_phone = contact_email = contact_website = None
        if venue.contact:
            contact_phone = venue.contact.phone
            contact_email = venue.contact.email
            contact_website = venue.contact.website

        # Flatten booking
        booking_reference = booking_requirements = booking_phone = booking_website = None
        if venue.booking:
            booking_reference = venue.booking.reference
            booking_requirements = venue.booking.requirements
            booking_phone = venue.booking.phone
            booking_website = venue.booking.website

        # JSON arrays
        def _json_list(lst: List) -> Optional[str]:
            return json.dumps(lst) if lst else None

        # Extra fields from model_extra (exclude metadata which we handle separately)
        extra = {}
        if venue.model_extra:
            for k, v in venue.model_extra.items():
                extra[k] = v
        # Also store metadata in extra_fields since it has extra subfields
        if venue.metadata:
            meta_dict = venue.metadata.model_dump()
            # Include non-standard metadata fields
            extra["metadata"] = meta_dict

        extra_fields_json = json.dumps(extra) if extra else None

        conn.execute(
            """INSERT INTO venues (
                id, trip_id, venue_id, canonical_name,
                address_street, address_city, address_region, address_country, address_postcode, address_raw,
                latitude, longitude,
                contact_phone, contact_email, contact_website,
                booking_reference, booking_requirements, booking_phone, booking_website,
                primary_cues, secondary_cues, camera_suggestions, negative_cues,
                reference_image_urls, sources, aliases, extra_fields
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                row_id, trip_id, venue.venue_id, venue.canonical_name,
                address_street, address_city, address_region, address_country, address_postcode, address_raw,
                None, None,  # latitude, longitude - not in current venue data
                contact_phone, contact_email, contact_website,
                booking_reference, booking_requirements, booking_phone, booking_website,
                _json_list(venue.primary_cues), _json_list(venue.secondary_cues),
                _json_list(venue.camera_suggestions), _json_list(venue.negative_cues),
                _json_list(venue.reference_image_urls), _json_list(venue.sources),
                _json_list(venue.aliases), extra_fields_json,
            ),
        )
        return row_id

    @staticmethod
    def get_venues_for_trip(conn: sqlite3.Connection, trip_id: str) -> Dict[str, Venue]:
        rows = conn.execute(
            "SELECT * FROM venues WHERE trip_id = ? ORDER BY venue_id", (trip_id,)
        ).fetchall()

        venues: Dict[str, Venue] = {}
        for row in rows:
            venues[row["venue_id"]] = _row_to_venue(row)
        return venues


def _row_to_venue(row: sqlite3.Row) -> Venue:
    """Reconstruct a Venue domain object from a database row."""
    # Reconstruct address
    address: Any = None
    if row["address_raw"]:
        address = row["address_raw"]
    elif any(row[f"address_{f}"] for f in ("street", "city", "region", "country", "postcode")):
        address = VenueAddress(
            street=row["address_street"],
            city=row["address_city"],
            region=row["address_region"],
            country=row["address_country"],
            postcode=row["address_postcode"],
        )

    # Reconstruct contact
    contact = None
    if any(row[f"contact_{f}"] for f in ("phone", "email", "website")):
        contact = VenueContact(
            phone=row["contact_phone"],
            email=row["contact_email"],
            website=row["contact_website"],
        )

    # Reconstruct booking
    booking = None
    if any(row[f"booking_{f}"] for f in ("reference", "requirements", "phone", "website")):
        booking = VenueBooking(
            reference=row["booking_reference"],
            requirements=row["booking_requirements"],
            phone=row["booking_phone"],
            website=row["booking_website"],
        )

    def _json_list(val: Optional[str]) -> List:
        return json.loads(val) if val else []

    # Build base kwargs
    kwargs: Dict[str, Any] = {
        "venue_id": row["venue_id"],
        "canonical_name": row["canonical_name"],
        "aliases": _json_list(row["aliases"]),
        "primary_cues": _json_list(row["primary_cues"]),
        "secondary_cues": _json_list(row["secondary_cues"]),
        "camera_suggestions": _json_list(row["camera_suggestions"]),
        "negative_cues": _json_list(row["negative_cues"]),
        "reference_image_urls": _json_list(row["reference_image_urls"]),
        "sources": _json_list(row["sources"]),
    }
    if address is not None:
        kwargs["address"] = address
    if contact is not None:
        kwargs["contact"] = contact
    if booking is not None:
        kwargs["booking"] = booking

    # Restore extra fields
    if row["extra_fields"]:
        extra = json.loads(row["extra_fields"])
        # Restore metadata from extra
        if "metadata" in extra:
            kwargs["metadata"] = VenueMetadata(**extra.pop("metadata"))
        # Merge remaining extra fields
        kwargs.update(extra)

    return Venue(**kwargs)


class EventRepository:
    # Fields that map directly from Event model to DB columns
    _DIRECT_FIELDS = {
        "event_heading", "kind", "location", "time_utc", "time_local",
        "timezone", "no_later_than", "venue_id", "travel_from", "travel_to",
        "description", "narrative", "image_path", "transition_from_prev",
        "emotional_triggers", "emotional_high_point",
    }

    @staticmethod
    def insert_event(conn: sqlite3.Connection, trip_id: str, event: Event) -> str:
        row_id = _new_uuid()

        # Collect extra fields (fields not in _DIRECT_FIELDS and not handled specially)
        _handled = EventRepository._DIRECT_FIELDS | {
            "who", "depends_on", "coordination_point", "hard_stop", "inferred",
            "duration", "duration_seconds",
        }
        extra = {}
        # Extra fields from model_extra
        if event.model_extra:
            for k, v in event.model_extra.items():
                if k not in _handled:
                    extra[k] = v

        # duration_seconds may be in model_extra (set by file_provider's parse_duration)
        duration_seconds = event.model_extra.get("duration_seconds") if event.model_extra else None

        # Also check declared fields that aren't in _DIRECT_FIELDS
        # duration is declared but we store duration_seconds in the DB
        if "duration_seconds" in (event.model_extra or {}):
            pass  # already captured above

        extra_fields_json = json.dumps(extra) if extra else None

        conn.execute(
            """INSERT INTO events (
                id, trip_id,
                event_heading, kind, location,
                time_utc, time_local, timezone, duration_seconds, no_later_than,
                who, depends_on,
                coordination_point, hard_stop, inferred,
                venue_id, travel_from, travel_to,
                description, narrative, image_path, transition_from_prev,
                emotional_triggers, emotional_high_point,
                extra_fields
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                row_id, trip_id,
                event.event_heading, event.kind, event.location,
                event.time_utc, event.time_local, event.timezone,
                duration_seconds, event.no_later_than,
                json.dumps(event.who) if event.who else None,
                json.dumps(event.depends_on) if event.depends_on else None,
                1 if event.coordination_point else (0 if event.coordination_point is not None else None),
                1 if event.hard_stop else (0 if event.hard_stop is not None else None),
                1 if event.inferred else (0 if event.inferred is not None else None),
                event.venue_id, event.travel_from, event.travel_to,
                event.description, event.narrative, event.image_path,
                event.transition_from_prev,
                event.emotional_triggers, event.emotional_high_point,
                extra_fields_json,
            ),
        )
        return row_id

    @staticmethod
    def get_events_for_trip(conn: sqlite3.Connection, trip_id: str) -> List[Event]:
        rows = conn.execute(
            "SELECT * FROM events WHERE trip_id = ? ORDER BY time_utc, created_at",
            (trip_id,),
        ).fetchall()
        return [_row_to_event(row) for row in rows]


def _row_to_event(row: sqlite3.Row) -> Event:
    """Reconstruct an Event domain object from a database row."""
    kwargs: Dict[str, Any] = {}

    # Direct string fields
    for field in EventRepository._DIRECT_FIELDS:
        val = row[field]
        if val is not None:
            kwargs[field] = val

    # JSON list fields
    who_val = row["who"]
    kwargs["who"] = json.loads(who_val) if who_val else []

    depends_val = row["depends_on"]
    kwargs["depends_on"] = json.loads(depends_val) if depends_val else []

    # Boolean fields (stored as INTEGER in SQLite, NULL means None)
    for bool_field in ("coordination_point", "hard_stop", "inferred"):
        val = row[bool_field]
        kwargs[bool_field] = bool(val) if val is not None else None

    # duration_seconds goes into extra (same as file_provider behavior)
    if row["duration_seconds"] is not None:
        kwargs["duration_seconds"] = row["duration_seconds"]

    # Restore extra fields
    if row["extra_fields"]:
        extra = json.loads(row["extra_fields"])
        kwargs.update(extra)

    return Event(**kwargs)

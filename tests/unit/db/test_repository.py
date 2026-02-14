"""Tests for database repositories."""

import json
import pytest
from itingen.db.schema import init_db
from itingen.db.connection import get_connection, transaction
from itingen.db.repository import (
    TripRepository,
    TravelerRepository,
    VenueRepository,
    EventRepository,
)
from itingen.core.domain.events import Event
from itingen.core.domain.venues import Venue, VenueAddress, VenueContact, VenueBooking


@pytest.fixture
def conn(tmp_path):
    db_path = str(tmp_path / "test.db")
    init_db(db_path)
    c = get_connection(db_path)
    yield c
    c.close()


@pytest.fixture
def trip_id(conn):
    """Insert a test trip and return its ID."""
    with transaction(conn):
        TripRepository.insert_trip(
            conn,
            trip_id="nz_2026",
            trip_name="NZ Trip",
            start_date="2026-01-01",
            end_date="2026-01-15",
            timezone="Pacific/Auckland",
        )
    return "nz_2026"


class TestTripRepository:
    def test_insert_and_get_trip(self, conn):
        with transaction(conn):
            TripRepository.insert_trip(
                conn,
                trip_id="nz_2026",
                trip_name="NZ Trip",
                start_date="2026-01-01",
                end_date="2026-01-15",
                timezone="Pacific/Auckland",
            )
        trip = TripRepository.get_trip(conn, "nz_2026")
        assert trip["id"] == "nz_2026"
        assert trip["trip_name"] == "NZ Trip"
        assert trip["timezone"] == "Pacific/Auckland"

    def test_insert_trip_with_optional_fields(self, conn):
        with transaction(conn):
            TripRepository.insert_trip(
                conn,
                trip_id="t1",
                trip_name="Trip",
                start_date="2026-01-01",
                end_date="2026-01-15",
                timezone="UTC",
                theme_config=json.dumps({"font": "serif"}),
                extra_config=json.dumps({"key": "val"}),
            )
        trip = TripRepository.get_trip(conn, "t1")
        assert json.loads(trip["theme_config"]) == {"font": "serif"}
        assert json.loads(trip["extra_config"]) == {"key": "val"}

    def test_get_nonexistent_trip(self, conn):
        trip = TripRepository.get_trip(conn, "nonexistent")
        assert trip is None


class TestTravelerRepository:
    def test_insert_and_get_travelers(self, conn, trip_id):
        with transaction(conn):
            TravelerRepository.insert_traveler(conn, trip_id, "t1", "David", "david")
            TravelerRepository.insert_traveler(conn, trip_id, "t2", "Clara", "clara")
        travelers = TravelerRepository.get_travelers_for_trip(conn, trip_id)
        assert len(travelers) == 2
        names = {t["name"] for t in travelers}
        assert names == {"David", "Clara"}

    def test_empty_travelers(self, conn, trip_id):
        travelers = TravelerRepository.get_travelers_for_trip(conn, trip_id)
        assert travelers == []


class TestVenueRepository:
    def test_insert_and_get_venues_as_domain_objects(self, conn, trip_id):
        venue = Venue(
            venue_id="ostro-brasserie",
            canonical_name="Ostro Brasserie & Bar",
            aliases=["Ostro"],
            primary_cues=["waterfront dining"],
            secondary_cues=[],
            camera_suggestions=[],
            negative_cues=[],
            reference_image_urls=[],
            sources=["https://example.com"],
        )
        with transaction(conn):
            VenueRepository.insert_venue(conn, trip_id, venue)
        venues = VenueRepository.get_venues_for_trip(conn, trip_id)
        assert "ostro-brasserie" in venues
        v = venues["ostro-brasserie"]
        assert isinstance(v, Venue)
        assert v.canonical_name == "Ostro Brasserie & Bar"
        assert v.aliases == ["Ostro"]
        assert v.primary_cues == ["waterfront dining"]
        assert v.sources == ["https://example.com"]

    def test_venue_with_structured_address(self, conn, trip_id):
        venue = Venue(
            venue_id="hotel-a",
            canonical_name="Hotel A",
            address=VenueAddress(
                street="123 Main St",
                city="Auckland",
                region="Auckland",
                country="New Zealand",
                postcode="1010",
            ),
        )
        with transaction(conn):
            VenueRepository.insert_venue(conn, trip_id, venue)
        venues = VenueRepository.get_venues_for_trip(conn, trip_id)
        v = venues["hotel-a"]
        assert isinstance(v.address, VenueAddress)
        assert v.address.street == "123 Main St"
        assert v.address.city == "Auckland"

    def test_venue_with_string_address(self, conn, trip_id):
        venue = Venue(
            venue_id="cafe-b",
            canonical_name="Cafe B",
            address="123 Queen Street, Auckland",
        )
        with transaction(conn):
            VenueRepository.insert_venue(conn, trip_id, venue)
        venues = VenueRepository.get_venues_for_trip(conn, trip_id)
        v = venues["cafe-b"]
        assert v.address == "123 Queen Street, Auckland"

    def test_venue_with_contact_and_booking(self, conn, trip_id):
        venue = Venue(
            venue_id="rest-c",
            canonical_name="Restaurant C",
            contact=VenueContact(phone="+64-9-123", email="info@c.com", website="https://c.com"),
            booking=VenueBooking(reference="BK123", requirements="Smart casual"),
        )
        with transaction(conn):
            VenueRepository.insert_venue(conn, trip_id, venue)
        venues = VenueRepository.get_venues_for_trip(conn, trip_id)
        v = venues["rest-c"]
        assert v.contact.phone == "+64-9-123"
        assert v.booking.reference == "BK123"

    def test_venue_extra_fields_roundtrip(self, conn, trip_id):
        venue = Venue(
            venue_id="ext-v",
            canonical_name="Extra Venue",
            custom_field="custom_value",
            another_field=42,
        )
        with transaction(conn):
            VenueRepository.insert_venue(conn, trip_id, venue)
        venues = VenueRepository.get_venues_for_trip(conn, trip_id)
        v = venues["ext-v"]
        assert v.model_extra.get("custom_field") == "custom_value"
        assert v.model_extra.get("another_field") == 42

    def test_empty_venues(self, conn, trip_id):
        venues = VenueRepository.get_venues_for_trip(conn, trip_id)
        assert venues == {}


class TestEventRepository:
    def test_insert_and_get_events_as_domain_objects(self, conn, trip_id):
        event = Event(
            event_heading="Uber to Airport",
            kind="drive",
            who=["john", "clara"],
            time_utc="2026-01-01T06:30:00Z",
            time_local="2026-01-01 06:30",
            location="Los Gatos → SJC",
            duration_seconds=1800,
            coordination_point=False,
            hard_stop=True,
            description="Uber ride to airport",
        )
        with transaction(conn):
            EventRepository.insert_event(conn, trip_id, event)
        events = EventRepository.get_events_for_trip(conn, trip_id)
        assert len(events) == 1
        e = events[0]
        assert isinstance(e, Event)
        assert e.event_heading == "Uber to Airport"
        assert e.kind == "drive"
        assert e.who == ["john", "clara"]
        assert e.time_utc == "2026-01-01T06:30:00Z"
        assert e.location == "Los Gatos → SJC"
        assert e.hard_stop is True
        assert e.coordination_point is False
        assert e.description == "Uber ride to airport"

    def test_event_with_venue_id(self, conn, trip_id):
        """Event with venue_id slug is preserved (no FK resolution in M1)."""
        event = Event(
            event_heading="Dinner at Ostro",
            kind="meal",
            venue_id="ostro-brasserie",
        )
        with transaction(conn):
            EventRepository.insert_event(conn, trip_id, event)
        events = EventRepository.get_events_for_trip(conn, trip_id)
        assert events[0].venue_id == "ostro-brasserie"

    def test_event_with_depends_on(self, conn, trip_id):
        event = Event(
            event_heading="Arrival",
            kind="flight_arrival",
            depends_on=["Flight Departure"],
        )
        with transaction(conn):
            EventRepository.insert_event(conn, trip_id, event)
        events = EventRepository.get_events_for_trip(conn, trip_id)
        assert events[0].depends_on == ["Flight Departure"]

    def test_event_extra_fields_roundtrip(self, conn, trip_id):
        event = Event(
            event_heading="Custom Event",
            kind="activity",
            source="manual",
            travel_mode="uber",
        )
        with transaction(conn):
            EventRepository.insert_event(conn, trip_id, event)
        events = EventRepository.get_events_for_trip(conn, trip_id)
        e = events[0]
        assert e.model_extra.get("source") == "manual"
        assert e.model_extra.get("travel_mode") == "uber"

    def test_event_duration_seconds_roundtrip(self, conn, trip_id):
        event = Event(
            event_heading="Long Drive",
            kind="drive",
            duration_seconds=5400,
        )
        with transaction(conn):
            EventRepository.insert_event(conn, trip_id, event)
        events = EventRepository.get_events_for_trip(conn, trip_id)
        assert events[0].model_extra.get("duration_seconds") == 5400

    def test_event_boolean_fields_roundtrip(self, conn, trip_id):
        event = Event(
            event_heading="Coord Point",
            kind="activity",
            coordination_point=True,
            hard_stop=False,
            inferred=True,
        )
        with transaction(conn):
            EventRepository.insert_event(conn, trip_id, event)
        events = EventRepository.get_events_for_trip(conn, trip_id)
        e = events[0]
        assert e.coordination_point is True
        assert e.hard_stop is False
        assert e.inferred is True

    def test_multiple_events_ordered_by_time(self, conn, trip_id):
        events_data = [
            Event(event_heading="Event B", kind="activity", time_utc="2026-01-02T10:00:00Z"),
            Event(event_heading="Event A", kind="activity", time_utc="2026-01-01T08:00:00Z"),
            Event(event_heading="Event C", kind="activity", time_utc="2026-01-03T12:00:00Z"),
        ]
        with transaction(conn):
            for e in events_data:
                EventRepository.insert_event(conn, trip_id, e)
        events = EventRepository.get_events_for_trip(conn, trip_id)
        headings = [e.event_heading for e in events]
        assert headings == ["Event A", "Event B", "Event C"]

    def test_empty_events(self, conn, trip_id):
        events = EventRepository.get_events_for_trip(conn, trip_id)
        assert events == []

    def test_event_with_none_optional_fields(self, conn, trip_id):
        """Events with all None optional fields should roundtrip cleanly."""
        event = Event(event_heading="Minimal Event")
        with transaction(conn):
            EventRepository.insert_event(conn, trip_id, event)
        events = EventRepository.get_events_for_trip(conn, trip_id)
        e = events[0]
        assert e.event_heading == "Minimal Event"
        assert e.kind is None
        assert e.who == []
        assert e.depends_on == []

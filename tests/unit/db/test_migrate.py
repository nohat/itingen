"""Tests for database migration from file-based trips."""

import pytest
from pathlib import Path
from itingen.db.schema import init_db
from itingen.db.connection import get_connection
from itingen.db.migrate import migrate_trip, MigrationError
from itingen.db.repository import TripRepository, TravelerRepository, VenueRepository, EventRepository


@pytest.fixture
def db_path(tmp_path):
    path = str(tmp_path / "test.db")
    init_db(path)
    return path


@pytest.fixture
def conn(db_path):
    c = get_connection(db_path)
    yield c
    c.close()


class TestMigrateTripNz2026:
    """Integration tests using the real nz_2026 trip data."""

    def test_migrate_creates_trip(self, db_path, conn):
        migrate_trip(Path("trips/nz_2026"), db_path)
        trip = TripRepository.get_trip(conn, "nz_2026")
        assert trip is not None
        assert trip["trip_name"] == "New Zealand Adventure 2026"
        assert trip["timezone"] == "Pacific/Auckland"

    def test_migrate_creates_travelers(self, db_path, conn):
        migrate_trip(Path("trips/nz_2026"), db_path)
        travelers = TravelerRepository.get_travelers_for_trip(conn, "nz_2026")
        names = {t["name"] for t in travelers}
        assert "David" in names
        assert "Clara" in names
        assert len(travelers) == 6

    def test_migrate_creates_venues(self, db_path, conn):
        migrate_trip(Path("trips/nz_2026"), db_path)
        venues = VenueRepository.get_venues_for_trip(conn, "nz_2026")
        assert len(venues) > 0
        # Check a known venue
        assert "auckland-downtown" in venues
        v = venues["auckland-downtown"]
        assert v.canonical_name == "Auckland Downtown Ferry Terminal"

    def test_migrate_creates_events(self, db_path, conn):
        migrate_trip(Path("trips/nz_2026"), db_path)
        events = EventRepository.get_events_for_trip(conn, "nz_2026")
        assert len(events) > 0
        # First event chronologically should have a heading
        headings = [e.event_heading for e in events if e.event_heading]
        assert len(headings) > 0

    def test_migrate_infers_dates(self, db_path, conn):
        migrate_trip(Path("trips/nz_2026"), db_path)
        trip = TripRepository.get_trip(conn, "nz_2026")
        # Trip dates should be inferred from events
        assert trip["start_date"] is not None
        assert trip["end_date"] is not None
        # nz_2026 starts 2025-12-28 and ends around 2026-01-11
        assert trip["start_date"] <= "2025-12-28"
        assert trip["end_date"] >= "2026-01-10"

    def test_migrate_preserves_event_who(self, db_path, conn):
        migrate_trip(Path("trips/nz_2026"), db_path)
        events = EventRepository.get_events_for_trip(conn, "nz_2026")
        # Find an event with who field
        events_with_who = [e for e in events if e.who]
        assert len(events_with_who) > 0
        # Check that who contains name strings
        for e in events_with_who:
            for name in e.who:
                assert isinstance(name, str)

    def test_migrate_preserves_event_extra_fields(self, db_path, conn):
        migrate_trip(Path("trips/nz_2026"), db_path)
        events = EventRepository.get_events_for_trip(conn, "nz_2026")
        # Events should have extra fields like 'source', 'travel_mode', 'id', 'date'
        events_with_extras = [e for e in events if e.model_extra]
        assert len(events_with_extras) > 0

    def test_migrate_idempotent_fails_on_duplicate(self, db_path):
        migrate_trip(Path("trips/nz_2026"), db_path)
        with pytest.raises(MigrationError, match="already exists"):
            migrate_trip(Path("trips/nz_2026"), db_path)


class TestMigrateTripExample:
    """Test with the example trip."""

    def test_migrate_example(self, db_path, conn):
        trip_dir = Path("trips/example")
        if not trip_dir.exists():
            pytest.skip("example trip not available")
        migrate_trip(trip_dir, db_path)
        trip = TripRepository.get_trip(conn, "example")
        assert trip is not None


class TestMigrateTripTokyo:
    """Test with the tokyo_city_break trip."""

    def test_migrate_tokyo(self, db_path, conn):
        trip_dir = Path("trips/tokyo_city_break")
        if not trip_dir.exists():
            pytest.skip("tokyo trip not available")
        migrate_trip(trip_dir, db_path)
        trip = TripRepository.get_trip(conn, "tokyo_city_break")
        assert trip is not None


class TestMigrationValidation:
    def test_nonexistent_trip_dir(self, db_path):
        with pytest.raises(MigrationError, match="not found"):
            migrate_trip(Path("trips/nonexistent"), db_path)

    def test_missing_config(self, db_path, tmp_path):
        trip_dir = tmp_path / "bad_trip"
        trip_dir.mkdir()
        with pytest.raises(MigrationError, match="config.yaml"):
            migrate_trip(trip_dir, db_path)

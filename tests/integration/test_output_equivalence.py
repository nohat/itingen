"""Output equivalence test: DB-backed provider produces same results as file-based.

This is the M1 acceptance test. For each sample trip, events and venues
loaded from the database must match those from the file provider.
"""

import pytest
from pathlib import Path
from itingen.db.schema import init_db
from itingen.db.migrate import migrate_trip
from itingen.providers.file_provider import LocalFileProvider
from itingen.providers.database_provider import DatabaseProvider


TRIP_DIRS = [
    Path("trips/nz_2026"),
    Path("trips/example"),
    Path("trips/tokyo_city_break"),
]


@pytest.fixture(scope="module")
def db_path(tmp_path_factory):
    """Create a database with all sample trips migrated."""
    tmp = tmp_path_factory.mktemp("equivalence")
    path = str(tmp / "test.db")
    init_db(path)
    for trip_dir in TRIP_DIRS:
        if trip_dir.exists():
            migrate_trip(trip_dir, path)
    return path


@pytest.mark.parametrize("trip_dir", TRIP_DIRS, ids=lambda d: d.name)
class TestOutputEquivalence:
    def test_event_count_matches(self, db_path, trip_dir):
        if not trip_dir.exists():
            pytest.skip(f"{trip_dir} not available")
        file_provider = LocalFileProvider(trip_dir)
        db_provider = DatabaseProvider(db_path, trip_dir.name)

        file_events = file_provider.get_events()
        db_events = db_provider.get_events()
        assert len(db_events) == len(file_events)

    def test_event_headings_match(self, db_path, trip_dir):
        if not trip_dir.exists():
            pytest.skip(f"{trip_dir} not available")
        file_provider = LocalFileProvider(trip_dir)
        db_provider = DatabaseProvider(db_path, trip_dir.name)

        file_headings = [e.event_heading for e in file_provider.get_events()]
        db_headings = [e.event_heading for e in db_provider.get_events()]
        # DB returns events sorted by time_utc; file provider returns in file order
        # Compare as sets since ordering may differ
        assert set(db_headings) == set(file_headings)

    def test_event_fields_match(self, db_path, trip_dir):
        """Core event fields match between file and DB providers."""
        if not trip_dir.exists():
            pytest.skip(f"{trip_dir} not available")
        file_provider = LocalFileProvider(trip_dir)
        db_provider = DatabaseProvider(db_path, trip_dir.name)

        file_events = {e.event_heading: e for e in file_provider.get_events()}
        db_events = {e.event_heading: e for e in db_provider.get_events()}

        for heading, file_event in file_events.items():
            db_event = db_events[heading]
            assert db_event.kind == file_event.kind, f"kind mismatch for '{heading}'"
            assert db_event.location == file_event.location, f"location mismatch for '{heading}'"
            assert db_event.time_utc == file_event.time_utc, f"time_utc mismatch for '{heading}'"
            assert db_event.time_local == file_event.time_local, f"time_local mismatch for '{heading}'"
            assert db_event.who == file_event.who, f"who mismatch for '{heading}'"
            assert db_event.depends_on == file_event.depends_on, f"depends_on mismatch for '{heading}'"
            assert db_event.venue_id == file_event.venue_id, f"venue_id mismatch for '{heading}'"
            assert db_event.description == file_event.description, f"description mismatch for '{heading}'"
            assert db_event.travel_from == file_event.travel_from, f"travel_from mismatch for '{heading}'"
            assert db_event.travel_to == file_event.travel_to, f"travel_to mismatch for '{heading}'"
            assert db_event.coordination_point == file_event.coordination_point, f"coordination_point mismatch for '{heading}'"
            assert db_event.hard_stop == file_event.hard_stop, f"hard_stop mismatch for '{heading}'"

    def test_venue_count_matches(self, db_path, trip_dir):
        if not trip_dir.exists():
            pytest.skip(f"{trip_dir} not available")
        file_provider = LocalFileProvider(trip_dir)
        db_provider = DatabaseProvider(db_path, trip_dir.name)

        file_venues = file_provider.get_venues()
        db_venues = db_provider.get_venues()
        assert len(db_venues) == len(file_venues)

    def test_venue_ids_match(self, db_path, trip_dir):
        if not trip_dir.exists():
            pytest.skip(f"{trip_dir} not available")
        file_provider = LocalFileProvider(trip_dir)
        db_provider = DatabaseProvider(db_path, trip_dir.name)

        assert set(db_provider.get_venues().keys()) == set(file_provider.get_venues().keys())

    def test_venue_names_match(self, db_path, trip_dir):
        if not trip_dir.exists():
            pytest.skip(f"{trip_dir} not available")
        file_provider = LocalFileProvider(trip_dir)
        db_provider = DatabaseProvider(db_path, trip_dir.name)

        file_venues = file_provider.get_venues()
        db_venues = db_provider.get_venues()

        for vid, file_venue in file_venues.items():
            db_venue = db_venues[vid]
            assert db_venue.canonical_name == file_venue.canonical_name, f"name mismatch for '{vid}'"
            assert db_venue.venue_id == file_venue.venue_id, f"venue_id mismatch for '{vid}'"

    def test_config_matches(self, db_path, trip_dir):
        if not trip_dir.exists():
            pytest.skip(f"{trip_dir} not available")
        file_provider = LocalFileProvider(trip_dir)
        db_provider = DatabaseProvider(db_path, trip_dir.name)

        file_config = file_provider.get_config()
        db_config = db_provider.get_config()

        assert db_config["trip_name"] == file_config["trip_name"]
        assert db_config["timezone"] == file_config["timezone"]
        assert len(db_config["people"]) == len(file_config["people"])

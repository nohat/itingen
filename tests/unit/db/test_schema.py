"""Tests for database schema creation and validation."""

import sqlite3
import pytest
from itingen.db.schema import init_db, SCHEMA_VERSION


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "test.db")


class TestInitDb:
    def test_creates_database_file(self, db_path):
        init_db(db_path)
        conn = sqlite3.connect(db_path)
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}
        conn.close()
        assert "trips" in tables
        assert "travelers" in tables
        assert "venues" in tables
        assert "events" in tables

    def test_creates_exactly_four_tables(self, db_path):
        init_db(db_path)
        conn = sqlite3.connect(db_path)
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}
        conn.close()
        # Should have exactly 4 user tables (sqlite_sequence may also exist)
        user_tables = tables - {"sqlite_sequence"}
        assert user_tables == {"trips", "travelers", "venues", "events"}

    def test_idempotent_init(self, db_path):
        """Calling init_db twice should not raise."""
        init_db(db_path)
        init_db(db_path)

    def test_schema_version_is_string(self):
        assert isinstance(SCHEMA_VERSION, str)
        assert SCHEMA_VERSION == "1"


class TestTripsTable:
    def test_trips_columns(self, db_path):
        init_db(db_path)
        conn = sqlite3.connect(db_path)
        cursor = conn.execute("PRAGMA table_info(trips)")
        columns = {row[1] for row in cursor.fetchall()}
        conn.close()
        expected = {
            "id", "trip_name", "start_date", "end_date", "timezone",
            "theme_config", "extra_config", "created_at", "updated_at",
        }
        assert columns == expected

    def test_trips_insert(self, db_path):
        init_db(db_path)
        conn = sqlite3.connect(db_path)
        conn.execute(
            "INSERT INTO trips (id, trip_name, start_date, end_date, timezone) "
            "VALUES (?, ?, ?, ?, ?)",
            ("nz_2026", "NZ Trip", "2026-01-01", "2026-01-15", "Pacific/Auckland"),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM trips WHERE id = 'nz_2026'").fetchone()
        conn.close()
        assert row is not None

    def test_trips_json_check_constraint(self, db_path):
        init_db(db_path)
        conn = sqlite3.connect(db_path)
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO trips (id, trip_name, start_date, end_date, timezone, theme_config) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                ("t1", "Trip", "2026-01-01", "2026-01-15", "UTC", "not-json"),
            )
        conn.close()


class TestTravelersTable:
    def test_travelers_columns(self, db_path):
        init_db(db_path)
        conn = sqlite3.connect(db_path)
        cursor = conn.execute("PRAGMA table_info(travelers)")
        columns = {row[1] for row in cursor.fetchall()}
        conn.close()
        expected = {"id", "trip_id", "name", "slug", "created_at"}
        assert columns == expected

    def test_travelers_foreign_key(self, db_path):
        init_db(db_path)
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO travelers (id, trip_id, name, slug) VALUES (?, ?, ?, ?)",
                ("uuid1", "nonexistent_trip", "Alice", "alice"),
            )
        conn.close()

    def test_travelers_unique_name_per_trip(self, db_path):
        init_db(db_path)
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute(
            "INSERT INTO trips (id, trip_name, start_date, end_date, timezone) "
            "VALUES (?, ?, ?, ?, ?)",
            ("t1", "Trip", "2026-01-01", "2026-01-15", "UTC"),
        )
        conn.execute(
            "INSERT INTO travelers (id, trip_id, name, slug) VALUES (?, ?, ?, ?)",
            ("uuid1", "t1", "Alice", "alice"),
        )
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO travelers (id, trip_id, name, slug) VALUES (?, ?, ?, ?)",
                ("uuid2", "t1", "Alice", "alice2"),
            )
        conn.close()


class TestVenuesTable:
    def test_venues_columns(self, db_path):
        init_db(db_path)
        conn = sqlite3.connect(db_path)
        cursor = conn.execute("PRAGMA table_info(venues)")
        columns = {row[1] for row in cursor.fetchall()}
        conn.close()
        assert "venue_id" in columns
        assert "canonical_name" in columns
        assert "address_street" in columns
        assert "extra_fields" in columns

    def test_venues_unique_venue_id_per_trip(self, db_path):
        init_db(db_path)
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute(
            "INSERT INTO trips (id, trip_name, start_date, end_date, timezone) "
            "VALUES (?, ?, ?, ?, ?)",
            ("t1", "Trip", "2026-01-01", "2026-01-15", "UTC"),
        )
        conn.execute(
            "INSERT INTO venues (id, trip_id, venue_id, canonical_name) "
            "VALUES (?, ?, ?, ?)",
            ("uuid1", "t1", "venue-a", "Venue A"),
        )
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO venues (id, trip_id, venue_id, canonical_name) "
                "VALUES (?, ?, ?, ?)",
                ("uuid2", "t1", "venue-a", "Different Name"),
            )
        conn.close()

    def test_venues_json_check_constraints(self, db_path):
        init_db(db_path)
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute(
            "INSERT INTO trips (id, trip_name, start_date, end_date, timezone) "
            "VALUES (?, ?, ?, ?, ?)",
            ("t1", "Trip", "2026-01-01", "2026-01-15", "UTC"),
        )
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO venues (id, trip_id, venue_id, canonical_name, primary_cues) "
                "VALUES (?, ?, ?, ?, ?)",
                ("uuid1", "t1", "v1", "V1", "not-json"),
            )
        conn.close()


class TestEventsTable:
    def test_events_columns(self, db_path):
        init_db(db_path)
        conn = sqlite3.connect(db_path)
        cursor = conn.execute("PRAGMA table_info(events)")
        columns = {row[1] for row in cursor.fetchall()}
        conn.close()
        # Check domain-model-aligned names
        assert "event_heading" in columns
        assert "kind" in columns
        assert "time_utc" in columns
        assert "who" in columns
        assert "depends_on" in columns
        assert "venue_uuid" in columns
        assert "venue_id" in columns
        # These should NOT exist (removed per A1/A3)
        assert "title" not in columns
        assert "type" not in columns
        assert "start_time" not in columns
        assert "participants" not in columns
        assert "source_artifact_id" not in columns

    def test_events_foreign_key_to_venues(self, db_path):
        init_db(db_path)
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute(
            "INSERT INTO trips (id, trip_name, start_date, end_date, timezone) "
            "VALUES (?, ?, ?, ?, ?)",
            ("t1", "Trip", "2026-01-01", "2026-01-15", "UTC"),
        )
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO events (id, trip_id, venue_uuid, event_heading) "
                "VALUES (?, ?, ?, ?)",
                ("evt1", "t1", "nonexistent_venue_uuid", "Test Event"),
            )
        conn.close()

    def test_events_json_who_constraint(self, db_path):
        init_db(db_path)
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute(
            "INSERT INTO trips (id, trip_name, start_date, end_date, timezone) "
            "VALUES (?, ?, ?, ?, ?)",
            ("t1", "Trip", "2026-01-01", "2026-01-15", "UTC"),
        )
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO events (id, trip_id, event_heading, who) "
                "VALUES (?, ?, ?, ?)",
                ("evt1", "t1", "Test", "not-json"),
            )
        conn.close()


class TestIndexes:
    def test_indexes_exist(self, db_path):
        init_db(db_path)
        conn = sqlite3.connect(db_path)
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indexes = {row[0] for row in cursor.fetchall()}
        conn.close()
        expected_indexes = {
            "idx_trips_dates",
            "idx_travelers_trip",
            "idx_travelers_trip_name",
            "idx_travelers_trip_slug",
            "idx_venues_trip",
            "idx_venues_location",
            "idx_events_trip",
            "idx_events_time",
            "idx_events_trip_time",
            "idx_events_venue",
            "idx_events_trip_kind",
            "idx_events_trip_heading",
        }
        assert expected_indexes.issubset(indexes)

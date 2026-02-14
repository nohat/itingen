"""Tests for DatabaseProvider."""

import pytest
from pathlib import Path
from itingen.db.schema import init_db
from itingen.db.migrate import migrate_trip
from itingen.providers.database_provider import DatabaseProvider
from itingen.core.domain.events import Event
from itingen.core.domain.venues import Venue


@pytest.fixture
def db_with_nz(tmp_path):
    db_path = str(tmp_path / "test.db")
    init_db(db_path)
    migrate_trip(Path("trips/nz_2026"), db_path)
    return db_path


class TestDatabaseProvider:
    def test_get_config(self, db_with_nz):
        provider = DatabaseProvider(db_with_nz, "nz_2026")
        config = provider.get_config()
        assert config["trip_name"] == "New Zealand Adventure 2026"
        assert config["timezone"] == "Pacific/Auckland"
        assert "people" in config
        assert len(config["people"]) == 6

    def test_get_events(self, db_with_nz):
        provider = DatabaseProvider(db_with_nz, "nz_2026")
        events = provider.get_events()
        assert len(events) > 0
        assert all(isinstance(e, Event) for e in events)
        # Should have headings
        headings = [e.event_heading for e in events if e.event_heading]
        assert len(headings) > 0

    def test_get_venues(self, db_with_nz):
        provider = DatabaseProvider(db_with_nz, "nz_2026")
        venues = provider.get_venues()
        assert len(venues) > 0
        assert all(isinstance(v, Venue) for v in venues.values())
        assert "auckland-downtown" in venues

    def test_nonexistent_trip_raises(self, db_with_nz):
        provider = DatabaseProvider(db_with_nz, "nonexistent")
        with pytest.raises(ValueError, match="not found"):
            provider.get_config()

    def test_config_people_match_file_provider(self, db_with_nz):
        """Config people should have same structure as file provider."""
        from itingen.providers.file_provider import LocalFileProvider
        file_provider = LocalFileProvider("trips/nz_2026")
        db_provider = DatabaseProvider(db_with_nz, "nz_2026")

        file_config = file_provider.get_config()
        db_config = db_provider.get_config()

        file_people = sorted(file_config["people"], key=lambda p: p["name"])
        db_people = sorted(db_config["people"], key=lambda p: p["name"])

        assert len(file_people) == len(db_people)
        for fp, dp in zip(file_people, db_people):
            assert fp["name"] == dp["name"]
            assert fp["slug"] == dp["slug"]

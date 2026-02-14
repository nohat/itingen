"""Tests for database connection management."""

import sqlite3
import pytest
from itingen.db.connection import get_connection, transaction
from itingen.db.schema import init_db


@pytest.fixture
def db_path(tmp_path):
    path = str(tmp_path / "test.db")
    init_db(path)
    return path


class TestGetConnection:
    def test_returns_connection(self, db_path):
        conn = get_connection(db_path)
        assert isinstance(conn, sqlite3.Connection)
        conn.close()

    def test_foreign_keys_enabled(self, db_path):
        conn = get_connection(db_path)
        result = conn.execute("PRAGMA foreign_keys").fetchone()
        conn.close()
        assert result[0] == 1

    def test_row_factory_set(self, db_path):
        conn = get_connection(db_path)
        conn.execute(
            "INSERT INTO trips (id, trip_name, start_date, end_date, timezone) "
            "VALUES (?, ?, ?, ?, ?)",
            ("t1", "Trip", "2026-01-01", "2026-01-15", "UTC"),
        )
        row = conn.execute("SELECT * FROM trips WHERE id = 't1'").fetchone()
        conn.close()
        # Row factory should allow key-based access
        assert row["id"] == "t1"
        assert row["trip_name"] == "Trip"


class TestTransaction:
    def test_commits_on_success(self, db_path):
        conn = get_connection(db_path)
        with transaction(conn):
            conn.execute(
                "INSERT INTO trips (id, trip_name, start_date, end_date, timezone) "
                "VALUES (?, ?, ?, ?, ?)",
                ("t1", "Trip", "2026-01-01", "2026-01-15", "UTC"),
            )
        row = conn.execute("SELECT * FROM trips WHERE id = 't1'").fetchone()
        conn.close()
        assert row is not None

    def test_rolls_back_on_exception(self, db_path):
        conn = get_connection(db_path)
        with pytest.raises(ValueError):
            with transaction(conn):
                conn.execute(
                    "INSERT INTO trips (id, trip_name, start_date, end_date, timezone) "
                    "VALUES (?, ?, ?, ?, ?)",
                    ("t1", "Trip", "2026-01-01", "2026-01-15", "UTC"),
                )
                raise ValueError("test error")
        row = conn.execute("SELECT * FROM trips WHERE id = 't1'").fetchone()
        conn.close()
        assert row is None

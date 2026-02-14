"""Database schema definition and initialization for itingen."""

import sqlite3

SCHEMA_VERSION = "1"

SCHEMA_SQL = """
-- trips: Central table for trip metadata and configuration
CREATE TABLE IF NOT EXISTS trips (
    id TEXT PRIMARY KEY,
    trip_name TEXT NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    timezone TEXT NOT NULL,
    theme_config TEXT
        CHECK(theme_config IS NULL OR json_valid(theme_config)),
    extra_config TEXT
        CHECK(extra_config IS NULL OR json_valid(extra_config)),
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_trips_dates ON trips(start_date, end_date);

-- travelers: People participating in a trip
CREATE TABLE IF NOT EXISTS travelers (
    id TEXT PRIMARY KEY,
    trip_id TEXT NOT NULL,
    name TEXT NOT NULL,
    slug TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    FOREIGN KEY (trip_id) REFERENCES trips(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_travelers_trip ON travelers(trip_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_travelers_trip_name ON travelers(trip_id, name);
CREATE UNIQUE INDEX IF NOT EXISTS idx_travelers_trip_slug ON travelers(trip_id, slug);

-- venues: Physical locations where events occur
CREATE TABLE IF NOT EXISTS venues (
    id TEXT PRIMARY KEY,
    trip_id TEXT NOT NULL,
    venue_id TEXT NOT NULL,
    canonical_name TEXT NOT NULL,

    -- Address (flattened from VenueAddress)
    address_street TEXT,
    address_city TEXT,
    address_region TEXT,
    address_country TEXT,
    address_postcode TEXT,
    address_raw TEXT,

    -- Geolocation
    latitude REAL,
    longitude REAL,

    -- Contact (flattened from VenueContact)
    contact_phone TEXT,
    contact_email TEXT,
    contact_website TEXT,

    -- Booking (flattened from VenueBooking)
    booking_reference TEXT,
    booking_requirements TEXT,
    booking_phone TEXT,
    booking_website TEXT,

    -- AI generation hints
    primary_cues TEXT
        CHECK(primary_cues IS NULL OR json_valid(primary_cues)),
    secondary_cues TEXT
        CHECK(secondary_cues IS NULL OR json_valid(secondary_cues)),
    camera_suggestions TEXT
        CHECK(camera_suggestions IS NULL OR json_valid(camera_suggestions)),
    negative_cues TEXT
        CHECK(negative_cues IS NULL OR json_valid(negative_cues)),
    reference_image_urls TEXT
        CHECK(reference_image_urls IS NULL OR json_valid(reference_image_urls)),
    sources TEXT
        CHECK(sources IS NULL OR json_valid(sources)),

    -- Metadata
    aliases TEXT
        CHECK(aliases IS NULL OR json_valid(aliases)),
    extra_fields TEXT
        CHECK(extra_fields IS NULL OR json_valid(extra_fields)),

    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),

    FOREIGN KEY (trip_id) REFERENCES trips(id) ON DELETE CASCADE,
    UNIQUE(trip_id, venue_id)
);

CREATE INDEX IF NOT EXISTS idx_venues_trip ON venues(trip_id);
CREATE INDEX IF NOT EXISTS idx_venues_location ON venues(latitude, longitude);

-- events: Time-bound activities in the itinerary
CREATE TABLE IF NOT EXISTS events (
    id TEXT PRIMARY KEY,
    trip_id TEXT NOT NULL,
    venue_uuid TEXT,

    -- Core identification (matches Event model field names)
    event_heading TEXT,
    kind TEXT,
    location TEXT,

    -- Timing (matches Event model field names)
    time_utc TEXT,
    time_local TEXT,
    timezone TEXT,
    duration_seconds INTEGER,
    no_later_than TEXT,

    -- Participation
    who TEXT
        CHECK(who IS NULL OR json_valid(who)),
    depends_on TEXT
        CHECK(depends_on IS NULL OR json_valid(depends_on)),

    -- Scheduling flags
    coordination_point INTEGER DEFAULT 0,
    hard_stop INTEGER DEFAULT 0,
    inferred INTEGER DEFAULT 0,

    -- Venue reference (original slug from event data)
    venue_id TEXT,

    -- Travel events
    travel_from TEXT,
    travel_to TEXT,

    -- Content
    description TEXT,
    narrative TEXT,
    image_path TEXT,
    transition_from_prev TEXT,

    -- Emotional annotations
    emotional_triggers TEXT,
    emotional_high_point TEXT,

    -- Extensibility
    extra_fields TEXT
        CHECK(extra_fields IS NULL OR json_valid(extra_fields)),

    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),

    FOREIGN KEY (trip_id) REFERENCES trips(id) ON DELETE CASCADE,
    FOREIGN KEY (venue_uuid) REFERENCES venues(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_events_trip ON events(trip_id);
CREATE INDEX IF NOT EXISTS idx_events_time ON events(time_utc);
CREATE INDEX IF NOT EXISTS idx_events_trip_time ON events(trip_id, time_utc);
CREATE INDEX IF NOT EXISTS idx_events_venue ON events(venue_uuid);
CREATE INDEX IF NOT EXISTS idx_events_trip_kind ON events(trip_id, kind);
CREATE INDEX IF NOT EXISTS idx_events_trip_heading ON events(trip_id, event_heading);
"""


def init_db(db_path: str) -> None:
    """Initialize the database schema. Idempotent (uses IF NOT EXISTS)."""
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA_SQL)
    conn.close()

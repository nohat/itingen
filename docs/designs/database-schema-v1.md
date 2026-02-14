# Database Schema v1 Design Document

**Status**: Approved - Revision 3
**Owner**: Engineering
**Created**: 2026-01-14

## Overview

This document specifies the SQLite database schema for itingen's transition from file-based storage (Markdown/YAML/JSON) to a relational database. The schema supports the core SPE (Source-Pipeline-Emitter) model for M1: DB-backed CLI.

### Design Goals

1. **Domain model alignment**: Column names match existing Pydantic field names exactly
2. **Simplicity**: Only build tables needed for M1 (4 tables, not 8)
3. **Portability**: Use SQLite-compatible SQL that can migrate to Postgres/MySQL
4. **Performance**: Index common query patterns (trip events, time-based queries)

### Scope

**In Scope (v1 / M1)**:
- Single-user local storage (SQLite file)
- Core trip/event/venue/traveler management
- DatabaseProvider producing identical output to LocalFileProvider

**Deferred to Future Milestones**:
- `artifacts`, `extractions` tables (M4: Artifact Intake)
- `cost_records` table (M3: Cost Tracking)
- `enrichment_jobs` table (M3: Enrichment Pipeline)
- Multi-user/tenant support
- Cloud database migration (Postgres/MySQL)
- Real-time sync, full-text search, chat history

### Architecture Decision: Keep Domain Field Names (A1)

The original schema doc renamed `event_heading→title`, `kind→type`, `time_utc→start_time`, `canonical_name→name`. This would break 50+ references across 20+ files and 46 test files.

**Decision**: Use domain model field names as DB column names. The code IS the spec. `type` shadows a Python builtin. The mapping layer adds complexity for zero user benefit.

---

## Schema Definition

### 1. `trips`

Central table for trip metadata and configuration.

```sql
CREATE TABLE trips (
    id TEXT PRIMARY KEY,                    -- User-facing slug, e.g., 'nz_2026'
    trip_name TEXT NOT NULL,                -- Display name, e.g., 'New Zealand Adventure 2026'
    start_date TEXT NOT NULL,               -- ISO 8601 date, e.g., '2026-01-20'
    end_date TEXT NOT NULL,                 -- ISO 8601 date, e.g., '2026-02-10'
    timezone TEXT NOT NULL,                 -- Canonical timezone, e.g., 'Pacific/Auckland'
    theme_config TEXT                       -- JSON: theme settings for rendering
        CHECK(theme_config IS NULL OR json_valid(theme_config)),
    extra_config TEXT                       -- JSON: any additional config fields
        CHECK(extra_config IS NULL OR json_valid(extra_config)),
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE INDEX idx_trips_dates ON trips(start_date, end_date);
```

**Mapping from LocalFileProvider**:
- Folder name (e.g., `nz_2026`) → `id`
- `config.yaml` `trip_name` → `trip_name`
- `config.yaml` `timezone` → `timezone`
- `config.yaml` `theme` (if present) → `theme_config`

---

### 2. `travelers`

People participating in a trip.

```sql
CREATE TABLE travelers (
    id TEXT PRIMARY KEY,                    -- UUID
    trip_id TEXT NOT NULL,
    name TEXT NOT NULL,                     -- Display name, e.g., 'David'
    slug TEXT NOT NULL,                     -- CLI identifier, e.g., 'david'
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    FOREIGN KEY (trip_id) REFERENCES trips(id) ON DELETE CASCADE
);

CREATE INDEX idx_travelers_trip ON travelers(trip_id);
CREATE UNIQUE INDEX idx_travelers_trip_name ON travelers(trip_id, name);
CREATE UNIQUE INDEX idx_travelers_trip_slug ON travelers(trip_id, slug);
```

**Mapping from LocalFileProvider**:
- `config.yaml` `people` array → `travelers` rows
- `people[].name` → `name`
- `people[].slug` → `slug`

---

### 3. `venues`

Physical locations where events occur.

```sql
CREATE TABLE venues (
    id TEXT PRIMARY KEY,                    -- UUID
    trip_id TEXT NOT NULL,
    venue_id TEXT NOT NULL,                 -- Original venue_id from domain model (slug)
    canonical_name TEXT NOT NULL,           -- Official name (matches Venue.canonical_name)

    -- Address (flattened from VenueAddress)
    address_street TEXT,
    address_city TEXT,
    address_region TEXT,
    address_country TEXT,
    address_postcode TEXT,
    address_raw TEXT,                       -- Original unstructured address string

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
    primary_cues TEXT                       -- JSON array
        CHECK(primary_cues IS NULL OR json_valid(primary_cues)),
    secondary_cues TEXT                     -- JSON array
        CHECK(secondary_cues IS NULL OR json_valid(secondary_cues)),
    camera_suggestions TEXT                 -- JSON array
        CHECK(camera_suggestions IS NULL OR json_valid(camera_suggestions)),
    negative_cues TEXT                      -- JSON array
        CHECK(negative_cues IS NULL OR json_valid(negative_cues)),
    reference_image_urls TEXT               -- JSON array
        CHECK(reference_image_urls IS NULL OR json_valid(reference_image_urls)),
    sources TEXT                            -- JSON array of verification URLs
        CHECK(sources IS NULL OR json_valid(sources)),

    -- Metadata
    aliases TEXT                            -- JSON array of alternative names
        CHECK(aliases IS NULL OR json_valid(aliases)),
    extra_fields TEXT                       -- JSON: captures extra="allow" fields
        CHECK(extra_fields IS NULL OR json_valid(extra_fields)),

    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),

    FOREIGN KEY (trip_id) REFERENCES trips(id) ON DELETE CASCADE,
    UNIQUE(trip_id, venue_id)
);

CREATE INDEX idx_venues_trip ON venues(trip_id);
CREATE INDEX idx_venues_location ON venues(latitude, longitude);
```

**Mapping from LocalFileProvider**:
- `venues/*.json` → `venues` rows
- `Venue.venue_id` → `venues.venue_id`
- `Venue.canonical_name` → `venues.canonical_name`
- `Venue.address` (Union[str, VenueAddress]) → `address_*` columns or `address_raw`
- `Venue.model_extra` → `extra_fields` JSON

---

### 4. `events`

Time-bound activities in the itinerary.

```sql
CREATE TABLE events (
    id TEXT PRIMARY KEY,                    -- UUID
    trip_id TEXT NOT NULL,
    venue_uuid TEXT,                        -- FK to venues.id (nullable)

    -- Core identification (matches Event model field names)
    event_heading TEXT,                     -- Matches Event.event_heading
    kind TEXT,                              -- Matches Event.kind
    location TEXT,                          -- Location string (may differ from venue)

    -- Timing (matches Event model field names)
    time_utc TEXT,                          -- Matches Event.time_utc
    time_local TEXT,                        -- Matches Event.time_local
    timezone TEXT,                          -- Event-specific timezone
    duration_seconds INTEGER,               -- Canonical duration (extra field from parse)
    no_later_than TEXT,                     -- Latest possible start time

    -- Participation
    who TEXT                                -- JSON array of traveler names (matches Event.who)
        CHECK(who IS NULL OR json_valid(who)),
    depends_on TEXT                         -- JSON array of event headings
        CHECK(depends_on IS NULL OR json_valid(depends_on)),

    -- Scheduling flags
    coordination_point INTEGER DEFAULT 0,   -- Boolean
    hard_stop INTEGER DEFAULT 0,            -- Boolean
    inferred INTEGER DEFAULT 0,             -- Boolean

    -- Venue reference (original slug from event data)
    venue_id TEXT,                          -- Original venue_id slug from Event.venue_id

    -- Travel events
    travel_from TEXT,
    travel_to TEXT,

    -- Content
    description TEXT,
    narrative TEXT,                         -- AI-generated narrative
    image_path TEXT,                        -- Path to generated image
    transition_from_prev TEXT,              -- Transition description

    -- Emotional annotations
    emotional_triggers TEXT,
    emotional_high_point TEXT,

    -- Extensibility
    extra_fields TEXT                       -- JSON: captures extra="allow" fields
        CHECK(extra_fields IS NULL OR json_valid(extra_fields)),

    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),

    FOREIGN KEY (trip_id) REFERENCES trips(id) ON DELETE CASCADE,
    FOREIGN KEY (venue_uuid) REFERENCES venues(id) ON DELETE SET NULL
);

CREATE INDEX idx_events_trip ON events(trip_id);
CREATE INDEX idx_events_time ON events(time_utc);
CREATE INDEX idx_events_trip_time ON events(trip_id, time_utc);
CREATE INDEX idx_events_venue ON events(venue_uuid);
CREATE INDEX idx_events_trip_kind ON events(trip_id, kind);
CREATE INDEX idx_events_trip_heading ON events(trip_id, event_heading);
```

**Key differences from original schema doc**:
- `event_heading` (not `title`) — matches `Event.event_heading`
- `kind` (not `type`) — matches `Event.kind`, avoids shadowing Python builtin
- `time_utc` (not `start_time`) — matches `Event.time_utc`
- `who` JSON array of names (not `participants` with UUIDs) — simpler for M1, matches `Event.who`
- `depends_on` as JSON array of headings (not UUIDs) — matches `Event.depends_on`
- `venue_uuid` for FK to venues table, `venue_id` for original slug
- No `source_artifact_id`, `is_suggested`, `is_confirmed` (deferred to M4)

**Mapping from LocalFileProvider**:
- `events/*.md` parsed events → `events` rows
- All Event model fields map directly by name
- `Event.model_extra` → `extra_fields` JSON

---

## Entity Relationship Diagram

```
┌─────────┐       ┌───────────┐
│  trips  │───1:N─│ travelers │
└────┬────┘       └───────────┘
     │
     │ 1:N                    1:N
     ▼                         │
┌─────────┐               ┌───┴────┐
│ events  │───────N:1─────│ venues │
└─────────┘               └────────┘
```

---

## Design Decisions

### Decision 1: Keep Domain Field Names (A1)

**Decision**: DB column names match Pydantic model field names exactly.

**Rationale**:
- Eliminates mapping layer complexity
- The code IS the spec — 50+ references across 20+ files use these names
- `type` shadows a Python builtin (`kind` is better)
- Zero user benefit from renaming

### Decision 2: Store `who` as Names, Not UUIDs

**Decision**: Store `who` as JSON array of traveler names (matching `Event.who`).

**Rationale**:
- M1 goal is identical output to file-based generation
- DatabaseProvider must return `Event` objects with `who: List[str]` of names
- UUID resolution adds complexity with no M1 benefit
- Can be enhanced in M2+ if needed

### Decision 3: Store `depends_on` as Headings

**Decision**: Store `depends_on` as JSON array of event heading strings.

**Rationale**:
- Matches `Event.depends_on` field format exactly
- DatabaseProvider returns same data as LocalFileProvider
- UUID resolution is a future optimization, not M1 requirement

### Decision 4: Venue Scope — Per-Trip

**Decision**: Keep venues **per-trip** for v1.

**Rationale**:
- No current requirement for cross-trip venue sharing
- Per-trip is simpler and sufficient
- Schema allows future migration to global venues if needed

### Decision 5: 4 Tables Only (A3)

**Decision**: M1 implements only `trips`, `travelers`, `venues`, `events`.

**Rationale**:
- Per project philosophy: "code that handles cases that 'might happen someday' is technical debt"
- `artifacts`, `extractions`, `cost_records`, `enrichment_jobs` are deferred to milestones where those features are built
- Each table will be added when its feature is implemented

---

## Migration Strategy

### Approach: One-Way Migration

Files → Database only. No reverse sync.

### Migration Pre-Flight Validation

| Source | Required Fields | Validation |
|--------|-----------------|------------|
| `config.yaml` | `trip_name`, `timezone`, `people` | Must exist |
| `people[]` | `name`, `slug` | Each person must have both |
| `venues/*.json` | `venue_id`, `canonical_name` | Must exist |
| `events/*.md` | `event_heading` | Each event must have heading |

**Trip Dates**: Current `config.yaml` files may not contain `start_date`/`end_date`. Migration infers from event `time_local` fields (earliest → start, latest → end). Fails if no datable events exist.

### Migration Process

1. Load data via existing `LocalFileProvider`
2. Resolve/infer trip dates
3. Insert trip row
4. Insert travelers
5. Insert venues (flatten nested objects)
6. Insert events (preserve all field values as-is)

---

## Changelog

- **2026-02-14 (Rev 3)**: Architecture re-examination for M1
  - Column names now match domain model fields exactly (Decision A1)
  - Removed tables 5-8 (artifacts, extractions, cost_records, enrichment_jobs) — deferred
  - Removed `source_artifact_id`, `is_suggested`, `is_confirmed` from events
  - `who` stored as names (not UUIDs), `depends_on` stored as headings (not UUIDs)
  - Removed `slug`, `description`, `venue_type`, `auto_created` from venues (not in domain model)
  - Removed `role`, `email`, `preferences` from travelers (not in config.yaml)
  - Removed `duration_raw`, `participants`, `participants_display` from events
  - Added `venue_uuid` FK column distinct from `venue_id` slug
  - Simplified scope to M1 only
- **2026-01-14 (Rev 2)**: Address review feedback
- **2026-01-14 (Rev 1)**: Initial draft

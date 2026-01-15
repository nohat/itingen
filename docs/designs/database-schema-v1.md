# Database Schema v1 Design Document

**Status**: Draft - Revision 2
**Owner**: Engineering
**Created**: 2026-01-14
**Related**: [TDD: Database](../product/TDD_DATABASE.md)

## Overview

This document specifies the SQLite database schema for itingen's transition from file-based storage (Markdown/YAML/JSON) to a relational database. The schema supports the core SPE (Source-Pipeline-Emitter) model while enabling new capabilities: agentic chat intake, artifact management, cost tracking, and background enrichment.

### Design Goals

1. **Domain model alignment**: Map existing Pydantic models (`Event`, `Venue`) to database tables
2. **TDD consistency**: Column names align with ratified TDD_DATABASE.md
3. **Portability**: Use SQLite-compatible SQL that can migrate to Postgres/MySQL
4. **Audit trail**: Track all AI extractions and data lineage
5. **Performance**: Index common query patterns (trip events, time-based queries)

### Scope

**In Scope (v1)**:
- Single-user local storage (SQLite file)
- Core trip/event/venue management
- Artifact intake and extraction audit
- Cost tracking and enrichment jobs

**Deferred to Future Versions**:
- Multi-user/tenant support
- Cloud database migration (Postgres/MySQL) - schema is portable
- Real-time sync or replication
- Full-text search
- Chat/conversation history storage
- OAuth token storage for connectors

---

## Schema Definition

### 1. `trips`

Central table for trip metadata and configuration.

```sql
CREATE TABLE trips (
    id TEXT PRIMARY KEY,                    -- User-facing slug, e.g., 'nz_2026'
    name TEXT NOT NULL,                     -- Display name, e.g., 'New Zealand 2026'
    start_date TEXT NOT NULL,               -- ISO 8601 date, e.g., '2026-01-20'
    end_date TEXT NOT NULL,                 -- ISO 8601 date, e.g., '2026-02-10'
    timezone TEXT NOT NULL,                 -- Canonical timezone, e.g., 'Pacific/Auckland'
    theme_config TEXT                       -- JSON: theme settings for rendering
        CHECK(theme_config IS NULL OR json_valid(theme_config)),
    enrichment_settings TEXT                -- JSON: hydrator configuration
        CHECK(enrichment_settings IS NULL OR json_valid(enrichment_settings)),
    cost_tracking_settings TEXT             -- JSON: cost tracking configuration
        CHECK(cost_tracking_settings IS NULL OR json_valid(cost_tracking_settings)),
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE INDEX idx_trips_dates ON trips(start_date, end_date);
```

**Field Notes**:
- `id`: Primary identifier used in CLI commands and URLs. Not a UUID.
- `timezone`: Used as default for all date/time conversions in this trip.
- `cost_tracking_settings`: Per TDD spec, stores cost tracking configuration.
- JSON blobs have `CHECK(json_valid(...))` constraints for data integrity.

**Mapping from LocalFileProvider**:
- `config.yaml` → `trips` row
- Folder name (e.g., `nz_2026`) → `id`
- `trip_name` → `name`
- `timezone` → `timezone`
- `theme` (if present) → `theme_config`

---

### 2. `travelers`

People participating in a trip.

```sql
CREATE TABLE travelers (
    id TEXT PRIMARY KEY,                    -- UUID
    trip_id TEXT NOT NULL,
    name TEXT NOT NULL,                     -- Display name, e.g., 'David'
    slug TEXT NOT NULL,                     -- CLI identifier, e.g., 'david'
    role TEXT,                              -- e.g., 'adult', 'child'
    email TEXT,                             -- For future notifications
    preferences TEXT                        -- JSON: dietary, accessibility, etc.
        CHECK(preferences IS NULL OR json_valid(preferences)),
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    FOREIGN KEY (trip_id) REFERENCES trips(id) ON DELETE CASCADE
);

CREATE INDEX idx_travelers_trip ON travelers(trip_id);
CREATE UNIQUE INDEX idx_travelers_trip_name ON travelers(trip_id, name);
CREATE UNIQUE INDEX idx_travelers_trip_slug ON travelers(trip_id, slug);
```

**Field Notes**:
- `slug`: Critical for CLI filtering (e.g., `--person david`). Derived from config.yaml `slug` field.
- `name`: Display name used in event `who` field matching.
- `preferences`: JSON blob for dietary restrictions, accessibility needs.
- Unique constraints on both `(trip_id, name)` and `(trip_id, slug)`.

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
    name TEXT NOT NULL,                     -- Official name (TDD: 'name')
    slug TEXT NOT NULL,                     -- URL-safe identifier
    description TEXT,                       -- Optional user-provided description

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
    venue_type TEXT,                        -- e.g., 'restaurant', 'hotel', 'attraction'
    auto_created INTEGER DEFAULT 0,         -- 1 if auto-created from event location
    extra_fields TEXT                       -- JSON: captures extra="allow" fields
        CHECK(extra_fields IS NULL OR json_valid(extra_fields)),

    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),

    FOREIGN KEY (trip_id) REFERENCES trips(id) ON DELETE CASCADE,
    UNIQUE(trip_id, venue_id)
);

CREATE INDEX idx_venues_trip ON venues(trip_id);
CREATE INDEX idx_venues_slug ON venues(trip_id, slug);
CREATE INDEX idx_venues_location ON venues(latitude, longitude);
```

**Field Notes**:
- `name`: Renamed from `canonical_name` to match TDD spec.
- `venue_id`: Preserves the original domain model identifier (e.g., `ostro-brasserie`).
- `description`: Added per TDD spec for user-provided venue notes.
- Nested objects (`VenueAddress`, `VenueContact`, `VenueBooking`) are flattened for query simplicity.
- `extra_fields`: Captures any additional fields from `extra="allow"` in the Pydantic model.
- All JSON arrays have validity constraints.

**Mapping from LocalFileProvider**:
- `venues/*.json` → `venues` rows
- `Venue.venue_id` → `venues.venue_id`
- `Venue.canonical_name` → `venues.name`
- `Venue.address` (Union[str, VenueAddress]) → `address_*` columns or `address_raw`

---

### 4. `events`

Time-bound activities in the itinerary.

```sql
CREATE TABLE events (
    id TEXT PRIMARY KEY,                    -- UUID
    trip_id TEXT NOT NULL,
    venue_id TEXT,                          -- FK to venues.id (nullable)

    -- Core identification (TDD naming)
    title TEXT,                             -- Human-readable title (TDD: 'title')
    type TEXT,                              -- Event type (TDD: 'type'): 'flight', 'meal', etc.
    location TEXT,                          -- Location string (may differ from venue)

    -- Timing
    start_time TEXT,                        -- ISO 8601 datetime in UTC (TDD: 'start_time')
    time_local TEXT,                        -- ISO 8601 datetime in local timezone
    timezone TEXT,                          -- Event-specific timezone override
    duration_seconds INTEGER,               -- Canonical duration representation
    duration_raw TEXT,                      -- Original duration string, e.g., '1h30m'
    no_later_than TEXT,                     -- Latest possible start time

    -- Participation
    participants TEXT                       -- JSON array of traveler IDs
        CHECK(participants IS NULL OR json_valid(participants)),
    participants_display TEXT               -- JSON array of names (denormalized for display)
        CHECK(participants_display IS NULL OR json_valid(participants_display)),
    depends_on TEXT                         -- JSON array of event IDs (resolved during migration)
        CHECK(depends_on IS NULL OR json_valid(depends_on)),

    -- Scheduling flags
    coordination_point INTEGER DEFAULT 0,   -- Boolean: requires traveler coordination
    hard_stop INTEGER DEFAULT 0,            -- Boolean: strict timing constraint
    inferred INTEGER DEFAULT 0,             -- Boolean: system-generated vs explicit

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

    -- Provenance
    source_artifact_id TEXT,                -- FK to artifacts (nullable)
    is_suggested INTEGER DEFAULT 0,         -- 1 if generated by enrichment
    is_confirmed INTEGER DEFAULT 1,         -- 0 if needs user approval

    -- Extensibility
    extra_fields TEXT                       -- JSON: captures extra="allow" fields
        CHECK(extra_fields IS NULL OR json_valid(extra_fields)),

    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),

    FOREIGN KEY (trip_id) REFERENCES trips(id) ON DELETE CASCADE,
    FOREIGN KEY (venue_id) REFERENCES venues(id) ON DELETE SET NULL,
    FOREIGN KEY (source_artifact_id) REFERENCES artifacts(id) ON DELETE SET NULL
);

CREATE INDEX idx_events_trip ON events(trip_id);
CREATE INDEX idx_events_time ON events(start_time);
CREATE INDEX idx_events_trip_time ON events(trip_id, start_time);
CREATE INDEX idx_events_venue ON events(venue_id);
CREATE INDEX idx_events_type ON events(trip_id, type);
CREATE INDEX idx_events_trip_title ON events(trip_id, title);
```

**Field Notes**:
- `title`: Renamed from `event_heading` to match TDD spec.
- `type`: Renamed from `kind` to match TDD spec.
- `start_time`: Renamed from `time_utc` to match TDD spec (still stores UTC).
- `participants`: JSON array of traveler **UUIDs** (resolved during migration).
- `participants_display`: Denormalized names for display without joins (per review recommendation).
- `depends_on`: JSON array of event **UUIDs** (resolved during migration, not heading strings).
- `duration_seconds` is the canonical duration (per AIDEV-DECISION in domain model).
- `idx_events_trip_title`: Added for event dependency resolution by heading.
- All JSON columns have validity constraints.

**Mapping from LocalFileProvider**:
- `events/*.md` parsed events → `events` rows
- `Event.event_heading` → `events.title`
- `Event.kind` → `events.type`
- `Event.time_utc` → `events.start_time`
- `Event.who` → resolve to traveler UUIDs → `participants`, cache names → `participants_display`
- `Event.depends_on` → resolve headings to event UUIDs during migration
- `Event.venue_id` → lookup `venues.venue_id`, store `venues.id` (UUID)

---

### 5. `artifacts`

Uploaded files and connector imports (email, calendar).

```sql
CREATE TABLE artifacts (
    id TEXT PRIMARY KEY,                    -- UUID
    trip_id TEXT NOT NULL,
    artifact_type TEXT NOT NULL,            -- 'attachment', 'gmail', 'calendar'
    file_path TEXT,                         -- Relative path in artifact archive
    file_size_bytes INTEGER,
    mime_type TEXT,                         -- e.g., 'application/pdf'
    original_filename TEXT,                 -- User-provided filename
    content_hash TEXT,                      -- SHA256 for deduplication
    source_metadata TEXT                    -- JSON: email headers, calendar event ID, etc.
        CHECK(source_metadata IS NULL OR json_valid(source_metadata)),
    uploaded_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),

    FOREIGN KEY (trip_id) REFERENCES trips(id) ON DELETE CASCADE,
    UNIQUE(trip_id, content_hash)
);

CREATE INDEX idx_artifacts_trip ON artifacts(trip_id);
CREATE INDEX idx_artifacts_hash ON artifacts(content_hash);
CREATE INDEX idx_artifacts_type ON artifacts(artifact_type);
```

**Field Notes**:
- File content stored on disk, not as database BLOBs.
- `content_hash` prevents duplicate uploads.
- `source_metadata` captures email headers or calendar event details.

---

### 6. `extractions`

AI extraction results (immutable audit trail).

```sql
CREATE TABLE extractions (
    id TEXT PRIMARY KEY,                    -- UUID
    artifact_id TEXT NOT NULL,
    extraction_type TEXT NOT NULL,          -- 'booking', 'event', 'location'
    extracted_data TEXT NOT NULL            -- JSON: structured extraction result
        CHECK(json_valid(extracted_data)),
    confidence_score REAL,                  -- 0.0 - 1.0
    model_used TEXT,                        -- e.g., 'gemini-2.0-flash'
    prompt_hash TEXT,                       -- Hash of prompt for version tracking
    extracted_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),

    FOREIGN KEY (artifact_id) REFERENCES artifacts(id) ON DELETE CASCADE
);

CREATE INDEX idx_extractions_artifact ON extractions(artifact_id);
CREATE INDEX idx_extractions_type ON extractions(extraction_type);
CREATE INDEX idx_extractions_model ON extractions(model_used);
```

**Field Notes**:
- Immutable: rows are never updated, only inserted.
- Multiple extractions per artifact (e.g., re-runs with improved prompts).
- `prompt_hash` enables tracking which prompt version was used.
- `idx_extractions_model`: Added per TDD spec for model usage analysis.

---

### 7. `cost_records`

Inference cost tracking for API calls.

```sql
CREATE TABLE cost_records (
    id TEXT PRIMARY KEY,                    -- UUID
    trip_id TEXT,                           -- FK to trips (nullable for global ops)
    event_id TEXT,                          -- FK to events (nullable)
    artifact_id TEXT,                       -- FK to artifacts (nullable)
    timestamp TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    operation TEXT NOT NULL,                -- e.g., 'extract_booking', 'enrich_maps'
    provider TEXT NOT NULL,                 -- 'gemini', 'openai', 'anthropic'
    model TEXT NOT NULL,                    -- Model identifier
    input_tokens INTEGER,
    output_tokens INTEGER,
    cost_usd REAL NOT NULL,
    duration_ms INTEGER,                    -- API call duration
    metadata TEXT                           -- JSON: request/response samples
        CHECK(metadata IS NULL OR json_valid(metadata)),

    FOREIGN KEY (trip_id) REFERENCES trips(id) ON DELETE CASCADE,
    FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE SET NULL,
    FOREIGN KEY (artifact_id) REFERENCES artifacts(id) ON DELETE SET NULL
);

CREATE INDEX idx_cost_trip ON cost_records(trip_id);
CREATE INDEX idx_cost_timestamp ON cost_records(timestamp);
CREATE INDEX idx_cost_operation ON cost_records(operation);
CREATE INDEX idx_cost_provider ON cost_records(provider);
CREATE INDEX idx_cost_trip_timestamp ON cost_records(trip_id, timestamp);
```

**Field Notes**:
- `idx_cost_provider`: Added per TDD spec for provider-level cost analysis.

---

### 8. `enrichment_jobs`

Background enrichment queue.

```sql
CREATE TABLE enrichment_jobs (
    id TEXT PRIMARY KEY,                    -- UUID
    trip_id TEXT NOT NULL,
    job_type TEXT NOT NULL,                 -- 'meal_inference', 'maps_hydrator', etc.
    status TEXT NOT NULL DEFAULT 'pending', -- 'pending', 'running', 'completed', 'failed'
    priority INTEGER DEFAULT 5,             -- 1 (highest) to 10 (lowest)
    input_data TEXT                         -- JSON: job parameters
        CHECK(input_data IS NULL OR json_valid(input_data)),
    result_data TEXT                        -- JSON: job output
        CHECK(result_data IS NULL OR json_valid(result_data)),
    error_message TEXT,                     -- If status='failed'
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    started_at TEXT,
    completed_at TEXT,

    FOREIGN KEY (trip_id) REFERENCES trips(id) ON DELETE CASCADE
);

CREATE INDEX idx_jobs_status ON enrichment_jobs(status, priority);
CREATE INDEX idx_jobs_trip ON enrichment_jobs(trip_id);
CREATE INDEX idx_jobs_type ON enrichment_jobs(job_type);
```

---

## Entity Relationship Diagram

```
┌─────────┐       ┌───────────┐       ┌────────┐
│  trips  │───1:N─│ travelers │       │ venues │
└────┬────┘       └───────────┘       └───┬────┘
     │                                    │
     │ 1:N                           1:N  │
     ▼                                    ▼
┌─────────┐                          ┌────────┐
│ events  │──────────────────────N:1─│ venues │
└────┬────┘                          └────────┘
     │
     │ N:1
     ▼
┌───────────┐       ┌─────────────┐
│ artifacts │───1:N─│ extractions │
└─────┬─────┘       └─────────────┘
      │
      │ 1:N (audit)
      ▼
┌──────────────┐
│ cost_records │
└──────────────┘

┌──────────────────┐
│ enrichment_jobs  │ (standalone queue)
└──────────────────┘
```

---

## Design Decisions

This section resolves the open questions from the initial draft.

### Decision 1: Participant Storage

**Decision**: Store traveler **UUIDs** with denormalized names.

```sql
participants TEXT,           -- JSON array of traveler UUIDs (canonical)
participants_display TEXT,   -- JSON array of names (denormalized for display)
```

**Rationale**:
- UUIDs enable renaming travelers without breaking event references
- Names are cached in `participants_display` for read-heavy queries
- Migration resolves `who` names to traveler UUIDs once
- Single-user system makes denormalization acceptable

### Decision 2: Venue Scope

**Decision**: Keep venues **per-trip** for v1.

**Rationale**:
- No current requirement for cross-trip venue sharing
- Global venues require merge/conflict resolution (complexity)
- Per-trip is simpler and sufficient for initial use cases
- Schema allows future migration to global venues if needed

### Decision 3: Event Dependencies

**Decision**: Resolve `depends_on` to **event UUIDs** during migration.

**Rationale**:
- Heading strings are fragile (renaming breaks references)
- UUIDs provide stable references
- Migration is the right time to resolve (has full event list context)
- DAL can validate that referenced events exist

---

## Migration Strategy

### Approach: One-Way Migration

Files → Database only. No reverse sync.

**Rationale**:
- File-based storage is being deprecated
- Bidirectional sync adds complexity with no benefit
- Users will interact via chat interface (not editing files)

### Migration Pre-Flight Validation

Before migration, the script **must** validate required data exists. Missing data causes migration failure with a clear error.

**Required Fields by Source**:

| Source | Required Fields | Validation |
|--------|-----------------|------------|
| `config.yaml` | `trip_name`, `timezone`, `people` | Must exist |
| `config.yaml` | `start_date`, `end_date` | **See note below** |
| `people[]` | `name`, `slug` | Each person must have both |
| `venues/*.json` | `venue_id`, `canonical_name` | Must exist |
| `events/*.md` | `event_heading` | Each event must have heading |

**Config Data Gap**: Current `config.yaml` files may not contain `start_date`/`end_date`. Migration handles this:

1. If `dates.start`/`dates.end` exist in config → use them
2. Else if `start_date`/`end_date` exist at root → use them
3. Else → **infer from event dates** (earliest event → start, latest → end)
4. If no events → **fail with clear error** requiring manual date entry

```python
def infer_trip_dates(events: list[Event]) -> tuple[str, str]:
    """Infer trip dates from event times. Fails if no events."""
    if not events:
        raise MigrationError(
            "Cannot infer trip dates: no events found. "
            "Please add 'start_date' and 'end_date' to config.yaml"
        )
    times = [e.time_utc for e in events if e.time_utc]
    if not times:
        raise MigrationError(
            "Cannot infer trip dates: no events have time_utc. "
            "Please add 'start_date' and 'end_date' to config.yaml"
        )
    return min(times)[:10], max(times)[:10]  # Extract date portion
```

### Migration Steps

1. **Pre-flight validation**:
   ```bash
   python -m itingen.db.migrate --trip-dir trips/nz_2026 --validate-only
   ```

2. **Initialize schema**:
   ```bash
   python -m itingen.db.init --db-path itingen.db
   ```

3. **Migrate trip**:
   ```bash
   python -m itingen.db.migrate \
       --trip-dir trips/nz_2026 \
       --db-path itingen.db
   ```

4. **Verify migration**:
   ```bash
   python -m itingen.cli generate \
       --trip nz_2026 \
       --provider database \
       --db-path itingen.db
   ```

### Migration Process Detail

```python
def migrate_trip(trip_dir: Path, db_path: str):
    """Migrate a trip from files to database."""

    # 1. Load and validate config
    config = load_config(trip_dir / 'config.yaml')
    validate_config(config)  # Fails fast on missing required fields

    # 2. Load all data
    venues = load_venues(trip_dir / 'venues')
    events = load_events(trip_dir / 'events')

    # 3. Resolve trip dates
    start_date, end_date = get_or_infer_dates(config, events)

    # 4. Insert trip
    trip_id = config.get('trip_id', trip_dir.name)
    insert_trip(db, trip_id, config['trip_name'], start_date, end_date, ...)

    # 5. Insert travelers, build name→UUID lookup
    traveler_lookup = {}  # name → UUID
    for person in config['people']:
        uuid = insert_traveler(db, trip_id, person['name'], person['slug'], ...)
        traveler_lookup[person['name']] = uuid

    # 6. Insert venues, build venue_id→UUID lookup
    venue_lookup = {}  # venue_id (slug) → UUID
    for venue in venues:
        uuid = insert_venue(db, trip_id, venue, ...)
        venue_lookup[venue.venue_id] = uuid

    # 7. First pass: insert events, build heading→UUID lookup
    event_lookup = {}  # heading → UUID
    for event in events:
        uuid = insert_event_pass1(db, trip_id, event, venue_lookup, traveler_lookup)
        event_lookup[event.event_heading] = uuid

    # 8. Second pass: resolve depends_on references
    for event in events:
        if event.depends_on:
            resolved_deps = [event_lookup[h] for h in event.depends_on if h in event_lookup]
            update_event_depends_on(db, event_lookup[event.event_heading], resolved_deps)
```

### Data Transformation Rules

| Source | Target | Transformation |
|--------|--------|---------------|
| `config.yaml` | `trips` | Direct field mapping |
| Folder name | `trips.id` | Use as trip_id |
| `config.yaml.people[]` | `travelers` | Array to rows, generate UUIDs |
| `people[].slug` | `travelers.slug` | Direct mapping |
| `venues/*.json` | `venues` | Flatten nested objects, preserve venue_id |
| `Venue.canonical_name` | `venues.name` | Rename |
| `events/*.md` | `events` | Parse Markdown, resolve references |
| `Event.event_heading` | `events.title` | Rename |
| `Event.kind` | `events.type` | Rename |
| `Event.time_utc` | `events.start_time` | Rename |
| `Event.who` | `events.participants` | Resolve names → UUIDs |
| `Event.who` | `events.participants_display` | Cache original names |
| `Event.depends_on` | `events.depends_on` | Resolve headings → UUIDs |
| `Event.venue_id` | `events.venue_id` | Lookup slug → UUID |
| `VenueAddress` | `venues.address_*` | Flatten object or preserve raw string |

---

## Index Strategy

### Primary Query Patterns

| Query | Index Used |
|-------|-----------|
| Get all events for a trip, sorted by time | `idx_events_trip_time` |
| Get events at a specific venue | `idx_events_venue` |
| Get all venues for a trip | `idx_venues_trip` |
| Lookup venue by slug | `idx_venues_slug` |
| Lookup traveler by slug | `idx_travelers_trip_slug` |
| Resolve event dependency by heading | `idx_events_trip_title` |
| Get pending enrichment jobs | `idx_jobs_status` |
| Get cost records for date range | `idx_cost_trip_timestamp` |
| Analyze costs by provider | `idx_cost_provider` |
| Analyze extractions by model | `idx_extractions_model` |

### Future Optimization

- Add covering indexes if SELECT queries become slow
- Consider materialized views for cost aggregations
- Profile real-world queries before adding more indexes

---

## Security Considerations

### API Keys and Secrets

**Requirement**: API keys and secrets **must not** be stored in the database.

- Google Maps API key → environment variable `GOOGLE_MAPS_API_KEY`
- Gemini API key → environment variable `GEMINI_API_KEY`
- Any future API keys → environment variables

### OAuth Tokens (Future)

When OAuth connectors are implemented (Gmail, Calendar):
- `refresh_token` should be encrypted at rest
- Consider separate `oauth_tokens` table with encryption
- Deferred to connector implementation phase

### Artifact File Access

- Artifact `file_path` is relative to a configured archive root
- DAL must validate paths (no path traversal: `..`, absolute paths)
- Files should be stored outside web-accessible directories

### SQL Injection Prevention

- All database access must use parameterized queries
- Never concatenate user input into SQL strings
- Repository pattern enforces this at the DAL layer

---

## Compatibility Notes

### SQLite-Specific Syntax

The schema uses SQLite-compatible syntax that may need adjustment for other databases:

| SQLite | Postgres/MySQL Equivalent |
|--------|--------------------------|
| `TEXT` for dates | `TIMESTAMP WITH TIME ZONE` |
| `INTEGER` for booleans | `BOOLEAN` |
| `strftime(...)` | `NOW()` or `CURRENT_TIMESTAMP` |
| `CHECK(json_valid(...))` | Postgres: `jsonb` type, MySQL: `JSON` type |
| No `AUTOINCREMENT` | `SERIAL` or `AUTO_INCREMENT` |

### Domain Model Compatibility

- `extra="allow"` fields from Pydantic models are stored in `extra_fields` JSON column
- JSON arrays (participants, depends_on, cues) are stored as TEXT with JSON encoding
- All timestamps are ISO 8601 strings (portable across databases)

---

## Test Strategy

Implementation should include:

1. **Schema validation tests**: Apply migrations to empty DB, verify tables exist with correct columns
2. **Constraint tests**: Verify FK constraints, unique constraints, JSON validity checks
3. **Migration tests**: Round-trip from sample `trips/` directory, verify data integrity
4. **Query performance tests**: Benchmark common query patterns with realistic data volumes
5. **Edge case tests**: Empty trips, missing optional fields, Unicode content

---

## Approval

**Approval Criteria**: Merge this document to `master` branch.

**Implementation Blocked Until**: This document exists in `master`.

---

## Changelog

- **2026-01-14 (Rev 2)**: Address review feedback
  - Added `travelers.slug` column with unique constraint
  - Renamed columns to match TDD: `title`, `type`, `start_time`, `name`
  - Added `trips.cost_tracking_settings` per TDD
  - Added missing indexes: `idx_travelers_trip_slug`, `idx_events_trip_title`, `idx_cost_provider`, `idx_extractions_model`
  - Added JSON validity `CHECK` constraints on all JSON columns
  - Added migration pre-flight validation section with config data gap handling
  - Resolved open questions with documented decisions
  - Added Security Considerations section
  - Added Test Strategy section
  - Added `venues.description` per TDD
  - Added `participants_display` denormalized column
  - Clarified scope (deferred items vs in-scope)
- **2026-01-14 (Rev 1)**: Initial draft

# TDD: Database - SQLite Schema & Migration Strategy

**Status**: Ratified  
**Owner**: Engineering  
**Last Updated**: 2026-01-14

## Executive Summary

This document defines the database schema for itingen's transition from file-based storage (Markdown/YAML) to SQLite. The schema is designed to support the agentic chat intake system, artifact management, cost tracking, and background enrichment pipelines.

**Key Design Decisions**:
- **SQLite first**: Start with SQLite for simplicity; migrate to cloud DB later (Postgres/MySQL)
- **One-way migration**: Files → Database (no reverse sync)
- **Immutable artifacts**: Original files never modified after upload
- **Audit trail**: All AI extractions logged with confidence scores

## Schema Design

### Core Tables

#### 1. `trips`

Stores trip metadata and configuration.

```sql
CREATE TABLE trips (
    id TEXT PRIMARY KEY,                    -- e.g., 'nz_2026'
    name TEXT NOT NULL,                     -- e.g., 'New Zealand Adventure'
    start_date TEXT NOT NULL,               -- ISO 8601 date
    end_date TEXT NOT NULL,                 -- ISO 8601 date
    timezone TEXT NOT NULL,                 -- e.g., 'Pacific/Auckland'
    theme_config TEXT,                      -- JSON blob for theme settings
    enrichment_settings TEXT,               -- JSON blob for enrichment config
    cost_tracking_settings TEXT,            -- JSON blob for cost tracking config
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_trips_dates ON trips(start_date, end_date);
```

**Design Notes**:
- `id` is user-facing slug (used in URLs, CLI commands)
- JSON blobs for flexible configuration (avoid schema churn)
- `timezone` is canonical for all date/time conversions

#### 2. `travelers`

Stores people on the trip.

```sql
CREATE TABLE travelers (
    id TEXT PRIMARY KEY,                    -- UUID
    trip_id TEXT NOT NULL,                  -- Foreign key to trips
    name TEXT NOT NULL,                     -- e.g., 'David'
    role TEXT,                              -- e.g., 'adult', 'child'
    email TEXT,                             -- Optional for notifications
    preferences TEXT,                       -- JSON blob for food prefs, etc.
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (trip_id) REFERENCES trips(id) ON DELETE CASCADE
);

CREATE INDEX idx_travelers_trip ON travelers(trip_id);
```

**Design Notes**:
- Supports multi-traveler trips
- `preferences` can store dietary restrictions, accessibility needs, etc.

#### 3. `venues`

Stores locations (restaurants, attractions, hotels).

```sql
CREATE TABLE venues (
    id TEXT PRIMARY KEY,                    -- UUID
    trip_id TEXT NOT NULL,                  -- Foreign key to trips
    name TEXT NOT NULL,                     -- e.g., 'Ostro Brasserie'
    slug TEXT NOT NULL,                     -- e.g., 'ostro-brasserie'
    address TEXT,                           -- Full address
    city TEXT,                              -- e.g., 'Auckland'
    country TEXT,                           -- e.g., 'New Zealand'
    latitude REAL,                          -- GPS coordinates
    longitude REAL,
    venue_type TEXT,                        -- e.g., 'restaurant', 'hotel', 'attraction'
    description TEXT,                       -- Optional user-provided description
    metadata TEXT,                          -- JSON blob for photos, tags, etc.
    auto_created INTEGER DEFAULT 1,         -- 1 if auto-created from event, 0 if manually added
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (trip_id) REFERENCES trips(id) ON DELETE CASCADE,
    UNIQUE(trip_id, slug)
);

CREATE INDEX idx_venues_trip ON venues(trip_id);
CREATE INDEX idx_venues_location ON venues(latitude, longitude);
CREATE INDEX idx_venues_slug ON venues(trip_id, slug);
```

**Design Notes**:
- Most venues are auto-created from event locations
- `auto_created` flag distinguishes user-curated venues from auto-generated
- Geocoding happens at creation time (cached, not recomputed)

#### 4. `events`

Stores time-bound activities.

```sql
CREATE TABLE events (
    id TEXT PRIMARY KEY,                    -- UUID
    trip_id TEXT NOT NULL,                  -- Foreign key to trips
    venue_id TEXT,                          -- Foreign key to venues (nullable)
    type TEXT NOT NULL,                     -- e.g., 'flight', 'meal', 'activity'
    title TEXT NOT NULL,                    -- e.g., 'Departure to Auckland'
    description TEXT,                       -- Optional details
    start_time TEXT NOT NULL,               -- ISO 8601 datetime (UTC)
    duration_seconds INTEGER,               -- Duration in seconds (nullable)
    participants TEXT,                      -- JSON array of traveler_ids
    location_override TEXT,                 -- If event location differs from venue
    metadata TEXT,                          -- JSON blob for flight numbers, confirmation codes, etc.
    is_suggested INTEGER DEFAULT 0,         -- 1 if generated by enrichment (tentative)
    is_confirmed INTEGER DEFAULT 1,         -- 0 if needs user approval
    source_artifact_id TEXT,                -- Foreign key to artifacts (nullable)
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (trip_id) REFERENCES trips(id) ON DELETE CASCADE,
    FOREIGN KEY (venue_id) REFERENCES venues(id) ON DELETE SET NULL,
    FOREIGN KEY (source_artifact_id) REFERENCES artifacts(id) ON DELETE SET NULL
);

CREATE INDEX idx_events_trip ON events(trip_id);
CREATE INDEX idx_events_time ON events(start_time);
CREATE INDEX idx_events_trip_time ON events(trip_id, start_time);
CREATE INDEX idx_events_venue ON events(venue_id);
CREATE INDEX idx_events_source ON events(source_artifact_id);
```

**Design Notes**:
- `start_time` is always UTC (converted for display using trip timezone)
- `duration_seconds` is nullable (some events don't have known duration)
- `participants` is JSON array (allows per-event attendance tracking)
- `is_suggested` flag marks events generated by enrichment (e.g., meal inference)
- `source_artifact_id` provides audit trail back to original confirmation

#### 5. `artifacts`

Stores uploaded files and connector imports.

```sql
CREATE TABLE artifacts (
    id TEXT PRIMARY KEY,                    -- UUID
    trip_id TEXT NOT NULL,                  -- Foreign key to trips
    artifact_type TEXT NOT NULL,            -- e.g., 'attachment', 'gmail', 'calendar'
    file_path TEXT,                         -- Relative path in artifact archive
    file_size_bytes INTEGER,                -- File size
    mime_type TEXT,                         -- e.g., 'application/pdf'
    original_filename TEXT,                 -- User-provided filename
    content_hash TEXT,                      -- SHA256 for deduplication
    source_metadata TEXT,                   -- JSON blob for email headers, calendar event ID, etc.
    uploaded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (trip_id) REFERENCES trips(id) ON DELETE CASCADE,
    UNIQUE(trip_id, content_hash)           -- Prevent duplicate uploads
);

CREATE INDEX idx_artifacts_trip ON artifacts(trip_id);
CREATE INDEX idx_artifacts_hash ON artifacts(content_hash);
CREATE INDEX idx_artifacts_type ON artifacts(artifact_type);
```

**Design Notes**:
- Files stored on disk (not in database blob)
- `content_hash` prevents duplicate uploads
- `source_metadata` captures email headers (from, subject, date) or calendar event details

#### 6. `extractions`

Stores AI extraction results (audit trail).

```sql
CREATE TABLE extractions (
    id TEXT PRIMARY KEY,                    -- UUID
    artifact_id TEXT NOT NULL,              -- Foreign key to artifacts
    extraction_type TEXT NOT NULL,          -- e.g., 'booking', 'event', 'location'
    extracted_data TEXT NOT NULL,           -- JSON blob of extracted structured data
    confidence_score REAL,                  -- 0.0 - 1.0 confidence
    model_used TEXT,                        -- e.g., 'gemini-2.0-flash-thinking-exp-01-21'
    prompt_hash TEXT,                       -- Hash of prompt used (for version tracking)
    extracted_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (artifact_id) REFERENCES artifacts(id) ON DELETE CASCADE
);

CREATE INDEX idx_extractions_artifact ON extractions(artifact_id);
CREATE INDEX idx_extractions_type ON extractions(extraction_type);
CREATE INDEX idx_extractions_model ON extractions(model_used);
```

**Design Notes**:
- Immutable audit log (never updated)
- Multiple extractions per artifact (e.g., re-run with improved prompt)
- `confidence_score` can be used for filtering low-quality extractions
- `prompt_hash` allows tracking which prompt version was used

#### 7. `cost_records`

Stores inference cost tracking.

```sql
CREATE TABLE cost_records (
    id TEXT PRIMARY KEY,                    -- UUID
    trip_id TEXT,                           -- Foreign key to trips (nullable for global operations)
    event_id TEXT,                          -- Foreign key to events (nullable)
    artifact_id TEXT,                       -- Foreign key to artifacts (nullable)
    timestamp TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    operation TEXT NOT NULL,                -- e.g., 'extract_booking', 'enrich_maps'
    provider TEXT NOT NULL,                 -- e.g., 'gemini', 'openai', 'anthropic'
    model TEXT NOT NULL,                    -- e.g., 'gemini-2.0-flash-thinking-exp-01-21'
    input_tokens INTEGER,                   -- Tokens sent to API
    output_tokens INTEGER,                  -- Tokens received from API
    cost_usd REAL NOT NULL,                 -- Estimated cost in USD
    duration_ms INTEGER,                    -- API call duration
    metadata TEXT,                          -- JSON blob for additional context
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

**Design Notes**:
- Tracks every API call with cost attribution
- `trip_id` nullable for global operations (e.g., venue geocoding shared across trips)
- `metadata` can store request/response samples for debugging

#### 8. `enrichment_jobs`

Stores background enrichment queue.

```sql
CREATE TABLE enrichment_jobs (
    id TEXT PRIMARY KEY,                    -- UUID
    trip_id TEXT NOT NULL,                  -- Foreign key to trips
    job_type TEXT NOT NULL,                 -- e.g., 'meal_inference', 'maps_hydrator'
    status TEXT NOT NULL DEFAULT 'pending', -- 'pending', 'running', 'completed', 'failed'
    priority INTEGER DEFAULT 5,             -- 1 (highest) to 10 (lowest)
    input_data TEXT,                        -- JSON blob of job parameters
    result_data TEXT,                       -- JSON blob of job output
    error_message TEXT,                     -- If status='failed'
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    started_at TEXT,
    completed_at TEXT,
    FOREIGN KEY (trip_id) REFERENCES trips(id) ON DELETE CASCADE
);

CREATE INDEX idx_jobs_status ON enrichment_jobs(status, priority);
CREATE INDEX idx_jobs_trip ON enrichment_jobs(trip_id);
CREATE INDEX idx_jobs_type ON enrichment_jobs(job_type);
```

**Design Notes**:
- Simple queue for async processing
- Worker processes poll for `status='pending'` jobs
- `priority` allows user-triggered enrichment to jump ahead of automatic enrichment

## Migration Strategy: Files → Database

### One-Way Migration

**Design Decision**: Migration is **one-way** (files → database). No reverse sync.

**Rationale**:
- File-based storage is being deprecated
- Bidirectional sync adds complexity with no benefit
- Users will interact via chat interface (not editing files)

### Migration Script

```python
# scripts/migrate_to_database.py

import sqlite3
import yaml
from pathlib import Path

def migrate_trip(trip_dir: Path, db_path: str):
    """Migrate a trip from file-based storage to SQLite."""
    conn = sqlite3.connect(db_path)
    
    # 1. Load config.yaml
    config = yaml.safe_load((trip_dir / 'config.yaml').read_text())
    
    # 2. Insert trip record
    conn.execute("""
        INSERT INTO trips (id, name, start_date, end_date, timezone, theme_config)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        config['trip_id'],
        config['trip_name'],
        config['dates']['start'],
        config['dates']['end'],
        config['timezone'],
        json.dumps(config.get('theme', {}))
    ))
    
    # 3. Load travelers from config
    for traveler in config.get('travelers', []):
        conn.execute("""
            INSERT INTO travelers (id, trip_id, name, role)
            VALUES (?, ?, ?, ?)
        """, (
            str(uuid.uuid4()),
            config['trip_id'],
            traveler['name'],
            traveler.get('role', 'adult')
        ))
    
    # 4. Load venues from venues.md
    venues = parse_venues_markdown(trip_dir / 'venues.md')
    for venue in venues:
        conn.execute("""
            INSERT INTO venues (id, trip_id, name, slug, address, latitude, longitude)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            str(uuid.uuid4()),
            config['trip_id'],
            venue['name'],
            venue['slug'],
            venue['address'],
            venue['latitude'],
            venue['longitude']
        ))
    
    # 5. Load events from events.md
    events = parse_events_markdown(trip_dir / 'events.md')
    for event in events:
        venue_id = lookup_venue(conn, config['trip_id'], event.get('venue_slug'))
        conn.execute("""
            INSERT INTO events (id, trip_id, venue_id, type, title, start_time, duration_seconds)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            str(uuid.uuid4()),
            config['trip_id'],
            venue_id,
            event['type'],
            event['title'],
            event['start_time'],
            event.get('duration_seconds')
        ))
    
    conn.commit()
    conn.close()
```

### Migration Runbook

1. **Backup files**: `tar -czf trips_backup.tar.gz trips/`
2. **Initialize database**: `python scripts/init_database.py`
3. **Run migration**: `python scripts/migrate_to_database.py --trip nz_2026`
4. **Verify**: `python -m itingen.cli generate --trip nz_2026 --db sqlite:///itingen.db`
5. **Archive files**: Move `trips/` to `trips_archive/`

## Database Access Layer

### Design Pattern: Repository Pattern

**Avoid**: Raw SQL queries scattered throughout codebase

**Prefer**: Centralized repository classes

```python
# src/itingen/db/repositories.py

class TripRepository:
    def __init__(self, db_path: str):
        self.conn = sqlite3.connect(db_path)
    
    def get_trip(self, trip_id: str) -> Trip:
        """Get trip by ID."""
        row = self.conn.execute(
            "SELECT * FROM trips WHERE id = ?", (trip_id,)
        ).fetchone()
        return Trip.from_row(row)
    
    def create_trip(self, trip: Trip) -> str:
        """Create new trip."""
        self.conn.execute("""
            INSERT INTO trips (id, name, start_date, end_date, timezone)
            VALUES (?, ?, ?, ?, ?)
        """, (trip.id, trip.name, trip.start_date, trip.end_date, trip.timezone))
        self.conn.commit()
        return trip.id

class EventRepository:
    def __init__(self, db_path: str):
        self.conn = sqlite3.connect(db_path)
    
    def get_events_for_trip(self, trip_id: str) -> list[Event]:
        """Get all events for a trip, ordered by start_time."""
        rows = self.conn.execute("""
            SELECT * FROM events 
            WHERE trip_id = ? 
            ORDER BY start_time
        """, (trip_id,)).fetchall()
        return [Event.from_row(row) for row in rows]
    
    def create_event(self, event: Event) -> str:
        """Create new event."""
        event_id = str(uuid.uuid4())
        self.conn.execute("""
            INSERT INTO events (id, trip_id, venue_id, type, title, start_time, duration_seconds)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (event_id, event.trip_id, event.venue_id, event.type, event.title, 
              event.start_time, event.duration_seconds))
        self.conn.commit()
        return event_id
```

### Transaction Management

```python
from contextlib import contextmanager

@contextmanager
def transaction(db_path: str):
    """Context manager for database transactions."""
    conn = sqlite3.connect(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

# Usage
with transaction('itingen.db') as conn:
    # Multiple operations in single transaction
    trip_repo = TripRepository(conn)
    event_repo = EventRepository(conn)
    
    trip_repo.create_trip(trip)
    for event in events:
        event_repo.create_event(event)
```

## Future Considerations (Deferred)

### Cloud Database Migration

**Not in current roadmap**, but design should not preclude future migration.

**Deferred Research Questions**:
1. **Which cloud DB?** Postgres (most features), MySQL (simplest), PlanetScale (scalable)?
2. **Schema changes?** SQLite → Postgres requires adjustments (e.g., TEXT → VARCHAR(255))
3. **Migration strategy?** Dump SQLite → bulk insert? Or real-time sync?
4. **Multi-tenancy?** Single database with `user_id` foreign key? Or database-per-user?

**Design for Flexibility**:
- Use repository pattern (swap out SQLite connection with Postgres connection)
- Avoid SQLite-specific SQL features (e.g., no `AUTOINCREMENT` keyword)
- Use ISO 8601 text dates (portable across databases)
- Test queries against both SQLite and Postgres (via Docker)

### Query Optimization

**Not needed yet** (single-user, small datasets), but plan ahead:

- Add indexes on common query patterns
- Use `EXPLAIN QUERY PLAN` to identify slow queries
- Consider materialized views for aggregations (e.g., cost summaries)
- Profile real-world usage to find bottlenecks

### Backup & Restore

**Minimal viable solution**:
```bash
# Backup
cp itingen.db itingen_backup_$(date +%Y%m%d).db

# Restore
cp itingen_backup_20260114.db itingen.db
```

**Future enhancements**:
- Automated daily backups (cron job or web app background task)
- Incremental backups (SQLite `.backup` command)
- Cloud backup (S3, Google Drive)

## Related Documentation

- [PRD: Input Modality](PRD_INPUT_MODALITY.md) - Agentic chat system that uses this database
- [North Star Vision](NORTH_STAR.md) - Product vision
- [Architecture](../ARCHITECTURE.md) - System design

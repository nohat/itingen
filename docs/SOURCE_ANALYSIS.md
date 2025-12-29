# Source Code Analysis: New Zealand Trip Itinerary Generator

**Analysis Date**: 2025-12-29
**Source Location**: `/Users/nohat/scaffold/`
**Total Code Analyzed**: ~12,379 lines across 19 Python modules

## Executive Summary

The New Zealand trip itinerary generation system is a sophisticated, **cache-first, AI-powered document generation pipeline** that transforms structured event data (Markdown) into polished, personalized travel itineraries with AI-generated narratives, images, and weather information.

**Key Architecture**:
- **Core Language**: Python 3
- **Primary Dependencies**: Google Gemini API, Google Maps API, ReportLab, WeatherSpark
- **Output Formats**: Markdown (itineraries), PDF (polished deliverables), JPEG (images)
- **Design Philosophy**: Fail-fast, cache-first, local-first, explicit over implicit

**Code Quality**: ~70% of the codebase is **generic and reusable** with minimal changes.

---

## Table of Contents
1. [Core Components/Modules](#1-core-componentsmodules)
2. [Data Structures](#2-data-structures)
3. [Algorithms & Key Logic](#3-algorithms--key-logic)
4. [Key Abstractions](#4-key-abstractions)
5. [Dependencies Between Modules](#5-dependencies-between-modules)
6. [Patterns Used](#6-patterns-used)
7. [NZ-Specific vs Generic/Reusable](#7-nz-specific-vs-genericreusable)
8. [Edge Cases & Constraints Handled](#8-edge-cases--constraints-handled)
9. [Recommendations for Extraction](#9-recommendations-for-extraction)
10. [Data Flow Summary](#10-data-flow-summary)

---

## 1. Core Components/Modules

### 1.1 Orchestration & Entry Points

#### `nz_trip_daily_itinerary.py` (1,548 lines)
**Role**: Main orchestrator and CLI entry point

**Responsibilities**:
- Event ingestion from per-day Markdown files
- Google Maps API enrichment for drive durations
- Person-specific filtering
- Markdown generation (group view + per-person fluent view)
- PDF generation orchestration (calls other modules)
- Gemini tone conversion (optional friendly tone)

**Key Functions**:
- `enrich_travel_events_with_maps()` - Add realistic drive times via Google Maps
- `group_events_by_date()` - Organize events chronologically
- `filter_events_for_person()` - Per-person event filtering
- `render_daily_markdown()` - Generate group itinerary
- `render_person_fluent_markdown()` - Generate per-person narrative itinerary
- `describe_transition_logistics()` - Generate transitions between events
- `describe_emotional_annotations()` - Add emotional context to stressful events

**Reusability**: 60% generic (orchestration logic), 40% NZ-specific (hardcoded paths, traveler names)

---

### 1.2 Event Data Management

#### `nz_trip_events_ingest.py` (294 lines)
**Role**: Parse and ingest event data from Markdown

**Responsibilities**:
- Load per-day event files from `events/YYYY-MM-DD.md`
- Parse event blocks into structured dictionaries
- Apply day-level metadata to events
- Support multi-file ingestion

**Key Functions**:
- `ingest_events_from_directory()` - Load all events from day files
- `parse_event_block()` - Parse individual event Markdown blocks
- `parse_list_field()`, `parse_scalar()`, `parse_bool()` - Field parsing

**Reusability**: 95% generic - only file path conventions are NZ-specific

---

#### `nz_trip_sort_events.py` (executable)
**Role**: Sort events within day files chronologically
**Reusability**: 100% generic

---

### 1.3 Venue Management System

#### `nz_trip_venue_lookup.py` (586 lines)
**Role**: Core venue document management

**Responsibilities**:
- Load/save venue documents (JSON format)
- Generate filesystem-safe venue slugs
- Fuzzy matching venues to events (Jaccard similarity)
- Venue schema validation

**Data Structure**: Venue documents store:
- `canonical_name` - Official venue name
- `aliases` - Alternative names for matching
- `venue_visual_description` - Multi-paragraph description
- `primary_cues`, `secondary_cues` - Visual elements for image generation
- `camera_suggestions` - Framing guidance
- `negative_cues` - What to avoid in images
- `metadata` - Timestamps, research method, version

**Key Functions**:
- `generate_venue_slug()` - Create slug from canonical name
- `find_venue_for_event()` - Match events to venues (explicit ID or fuzzy)
- `save_venue()`, `load_venue()` - Persistence
- `validate_venue_schema()` - Schema validation

**Reusability**: 100% generic - venue system is trip-agnostic

---

**Supporting Venue Tools** (all 100% generic):
- `nz_trip_venue_list.py` - List/filter venues
- `nz_trip_venue_create.py` - Interactive venue creation
- `nz_trip_venue_enhance.py` - Enhance venues with cached research
- `nz_trip_venue_cleanup.py` - Identify bogus/duplicate venues
- `nz_trip_venue_migrate.py` - Migrate from event cache to venue docs
- `nz_trip_venue_migrate_builtins.py` - Migrate hardcoded venues

---

### 1.4 AI Content Generation

#### `nz_trip_event_narratives.py` (3,500+ lines)
**Role**: AI-powered content and image generation

**Responsibilities**:
- Generate event narratives (Gemini)
- Generate daily summaries (Gemini)
- Generate day taglines (Gemini structured output)
- Generate weather prose summaries (Gemini)
- Generate day banner images (Imagen or Gemini Image)
- Generate event thumbnail images (Gemini Image)
- Venue research (Gemini + Search for visual cues)
- Prompt synthesis for thumbnails

**Key Functions**:
- `generate_event_narratives()` - Per-event narrative text
- `generate_daily_summary()` - Day overview paragraph
- `generate_day_tagline_structured()` - Structured cities + items
- `generate_day_banner_image()` - 16:9 banner image
- `generate_event_thumbnail_images()` - Per-event thumbnails
- `generate_weather_prose_summary()` - Weather narrative

**Caching Strategy**:
- Fingerprint-based cache keys (event hash + prompt version + model config)
- Separate caches for prompts, images, research
- EXIF metadata embedding for image tracking

**Reusability**: 80% generic (AI integration patterns), 20% NZ-specific (city normalization, hardcoded place names)

---

### 1.5 PDF Rendering

#### `nz_trip_pdf_render.py` (1,400+ lines)
**Role**: ReportLab-based PDF layout and rendering

**Responsibilities**:
- Font management (Noto Sans for Māori macrons)
- Material Design icon rendering
- PDF document structure (header, banner, events, weather)
- Image scaling ("contain" mode for banners)
- Event card layout with thumbnails

**Key Classes**:
- `PdfTheme` - Color palette and spacing
- `_KindIconCircle` - Event type icons
- `_BannerImage` - Banner image flowable
- `_EventThumb` - Event thumbnail flowable
- `_HeroBanner` - Hero header section

**Key Functions**:
- `render_person_day_pdf()` - Main entry point
- `_make_weather_card()` - Weather information card
- `_event_row()` - Individual event layout

**Reusability**: 90% generic (PDF layout engine), 10% NZ-specific (Māori font requirements, specific theme colors)

---

#### `nz_trip_render.py` (118 lines)
**Role**: High-level PDF rendering wrapper
**Reusability**: 100% generic

---

### 1.6 Asset Management

#### `nz_trip_assets.py`
**Role**: Ensure all expensive assets are generated/cached
**Purpose**: Pre-generate AI content, images, weather data before PDF rendering
**Used by**: Makefile build system
**Reusability**: 100% generic pattern

---

### 1.7 External Integrations

#### `maps_trip_planner.py`
**Role**: Google Maps Directions API integration
**Purpose**: Enrich drive events with realistic durations/distances
**Caching**: Local JSON cache for route summaries
**Reusability**: 100% generic

---

#### `weatherspark_typical_weather.py`
**Role**: Weather data retrieval
**Purpose**: Fetch typical weather for day/location rendering
**Reusability**: 100% generic

---

#### `gemini_tone_converter.py`
**Role**: Convert Markdown to friendly conversational tone
**Purpose**: Optional post-processing of itinerary text
**Reusability**: 100% generic

---

## 2. Data Structures

### 2.1 Event Dictionary

**Source**: Parsed from Markdown event blocks

```python
{
    # Identity
    "id": "2025-12-31T1100-wine-Tantalus",
    "event_heading": "Wine tasting – Tantalus Estate",
    "date": "2025-12-31",

    # Timing
    "time_local": "2025-12-31 11:00",
    "time_utc": "2025-12-30T22:00Z",
    "timezone": "NZDT",
    "no_later_than": "2025-12-31 11:00",
    "duration": "1h00m",
    "duration_seconds": 3600,
    "duration_text": "1 hour",

    # Classification
    "kind": "activity",  # activity, meal, drive, ferry, lodging_checkin, flight_departure, etc.
    "who": ["david", "diego", "john", "clara", "alex", "stephanie"],

    # Location
    "location": "Tantalus Estate, 70-72 Onetangi Rd, Waiheke Island",
    "venue_id": "tantalus-estate-waiheke",  # Optional explicit venue link

    # Travel
    "travel_mode": "drive",  # drive, ferry, flight, uber, walk
    "travel_from": "Matiatia Wharf ferry terminal",
    "travel_to": "Tantalus Estate",
    "driver": "John",
    "parking": "in the vineyard parking lot",

    # Constraints
    "coordination_point": true,  # Group must be together
    "hard_stop": true,  # Must arrive by deadline
    "depends_on": ["2025-12-31T0955-Waiheke-car-rental-pickup"],
    "lock_duration": true,  # Don't override duration with Maps API

    # Content
    "description": "Tasting reservation at Tantalus Estate.",
    "notes": "Reservation at 11:00am.",
    "meal": "lunch",
    "transition_from_prev": "After the ferry, walk to the rental car...",

    # Metadata
    "source": "trip_updates",
    "inferred": false,

    # AI-Generated (added during processing)
    "narrative": "You'll enjoy a wine tasting at Tantalus Estate...",
    "thumb_image_path": "/path/to/thumbnail.jpg"
}
```

**Key Insight**: Events are incrementally enriched through the pipeline (parse → Maps API → venue matching → AI generation → rendering).

---

### 2.2 Venue Document

**Format**: JSON files in `scaffold-data/data/nz_trip_venues/`

```json
{
  "venue_id": "tantalus-estate-waiheke",
  "canonical_name": "Tantalus Estate Vineyard & Winery (Waiheke Island)",
  "aliases": [
    "Tantalus",
    "Tantalus Estate",
    "Tantalus Vineyard"
  ],
  "location": {
    "region": "Waiheke Island",
    "country": "New Zealand",
    "coordinates": null
  },
  "venue_visual_description": "Multi-paragraph textual description...",
  "primary_cues": [
    "modern cellar door silhouette",
    "vineyard rows on gentle hillside",
    "wide veranda / terrace view"
  ],
  "secondary_cues": [
    "Waiheke Island coastal light",
    "clean contemporary winery architecture"
  ],
  "camera_suggestions": [
    "macro close-up",
    "three-quarter view"
  ],
  "negative_cues": [
    "no text",
    "no logos",
    "no generic flat vineyard field",
    "no airplane"
  ],
  "reference_image_urls": [],
  "sources": [],
  "metadata": {
    "created_at": "2025-12-15T22:23:20.994690+00:00",
    "updated_at": "2025-12-15T22:31:01.325376+00:00",
    "research_method": "builtin+gemini",
    "research_version": "v3",
    "notes": "Migrated from hardcoded builtin..."
  }
}
```

**Key Insight**: Venues are persistent, reusable research artifacts that dramatically improve image quality and reduce API costs.

---

### 2.3 Day Tagline (Structured Output)

**Generated by Gemini structured output**

```python
{
  "cities": ["Auckland", "Waiheke Island"],
  "items": [
    "Morning ferry to Waiheke",
    "Wine tasting at Tantalus",
    "Lunch at Man O' War",
    "New Year's Eve dinner at Casita Miro"
  ]
}
```

---

### 2.4 Weather Data

**Retrieved from WeatherSpark API**

```python
{
  "location": "Queenstown",
  "date": "2026-01-07",
  "high_temp_f": 72,
  "low_temp_f": 54,
  "conditions": "Partly cloudy",
  "precipitation_chance": 20,
  # ... additional fields
}
```

---

## 3. Algorithms & Key Logic

### 3.1 Event Chronological Sorting

**Location**: `group_events_by_date()` in `nz_trip_daily_itinerary.py`

**Algorithm**:
1. For each event, extract sort key:
   - Prefer `time_utc` (UTC timestamp)
   - Fallback to `time_local` (parsed datetime)
   - Fallback to `no_later_than` (deadline)
   - Fallback to `dt.datetime.max` (untimed events last)
   - Tiebreaker: `id` or `event_heading`
2. Sort events globally by `(date, sort_key)`
3. Group into `OrderedDict[date_str, List[event]]`

**Edge Cases**:
- Untimed events placed at end of day
- Cross-date-line handling (use UTC for flights)
- Sub-group splits (John/Clara vs David/Diego/Alex/Stephanie)

**Reusability**: 100% generic

---

### 3.2 Person-Specific Filtering

**Location**: `filter_events_for_person()` in `nz_trip_daily_itinerary.py`

**Algorithm**:
1. Normalize person identifier (lowercase, strip)
2. For each event:
   - Extract `who` field (string or list)
   - Normalize all `who` values
   - Include if:
     - Target person in `who` list, OR
     - `"group"` in `who` list, OR
     - `"all"` in `who` list
3. Return filtered events

**Use Case**: Generate per-person itineraries for David, Diego, John, Clara, Alex, Stephanie

**Reusability**: 100% generic

---

### 3.3 Transition Logistics Generation

**Location**: `describe_transition_logistics()` in `nz_trip_daily_itinerary.py`

**Algorithm**:
1. Check for explicit `transition_from_prev` override → return if present
2. Extract previous and current event kinds, modes, locations
3. Pattern matching (cascading if/elif):
   - Drive → airport buffer
   - Airport buffer → flight departure
   - Flight departure → flight arrival (no transition needed)
   - Flight arrival → arrivals buffer
   - Ferry → drive
   - etc. (20+ patterns)
4. Inject driver/parking details if present
5. **Fail-fast**: If no pattern matches, raise error (force explicit handling)

**Design Philosophy**:
- No generic fallback text
- Forces explicit transitions for all event type combinations
- Ensures high-quality narrative descriptions

**Reusability**: 80% generic (pattern matching framework), 20% NZ-specific (specific event type combinations)

---

### 3.4 Venue Fuzzy Matching

**Location**: `find_venue_for_event()` in `nz_trip_venue_lookup.py`

**Algorithm**:
1. **Strategy 1 (Explicit)**: Check event for `venue_id` field → load directly
2. **Strategy 2 (Fuzzy)**:
   - Collect search texts from `location`, `event_heading`, `description`, `travel_to`
   - Combine into single string
   - For each venue:
     - Tokenize canonical name (extract words, filter stopwords)
     - Tokenize each alias
     - Calculate Jaccard similarity: `|tokens1 ∩ tokens2| / |tokens1 ∪ tokens2|`
   - Return best match if score >= threshold (default 0.8)

**Normalization**:
- Remove street addresses (regex patterns)
- Remove parenthetical suffixes
- Remove city/region suffixes
- Case-insensitive

**Reusability**: 100% generic

---

### 3.5 Venue Slug Generation

**Location**: `generate_venue_slug()` in `nz_trip_venue_lookup.py`

**Algorithm**:
1. Extract location from parentheses (e.g., "(Waiheke Island)" → "waiheke")
2. Remove location stopwords ("island", "resort", "hotel", etc.)
3. Tokenize venue name (word boundaries)
4. Remove name stopwords ("the", "and", "vineyard", "winery", etc.)
5. Keep first `max_tokens` significant tokens
6. Combine name tokens + location tokens
7. Lowercase, hyphenate, clean up double hyphens

**Example**:
- Input: `"Tantalus Estate Vineyard & Winery (Waiheke Island)"`
- Output: `"tantalus-estate-waiheke"`

**Reusability**: 90% generic (stopwords might need customization for different languages/regions)

---

### 3.6 Maps API Enrichment

**Location**: `enrich_travel_events_with_maps()` in `nz_trip_daily_itinerary.py`

**Algorithm**:
1. Load route cache from JSON
2. For each event:
   - Skip if `kind != "drive"` or `lock_duration == true`
   - Extract `travel_from`, `travel_to`, `travel_mode`, `time_local`
   - Build cache key: `origin|destination|mode|departure_time|`
   - Check cache → return cached if present
   - Call Google Maps Directions API
   - Extract `duration_seconds`, `duration_text`
   - Update event fields
   - Save to cache
3. Save cache (dirty check)

**Caching**: Persistent JSON file with stable keys

**Reusability**: 100% generic

---

### 3.7 Image Fingerprinting & Cache Reuse

**Location**: `nz_trip_event_narratives.py`

**Algorithm**:
1. Build payload: `{prompt, event_model, aspect_ratio, ref_hashes, ...}`
2. Serialize to stable JSON (sorted keys, no whitespace)
3. Compute SHA256 fingerprint of payload
4. Check cache dir for `<fingerprint>.jpg`
5. If found → verify metadata matches → reuse
6. If not found → generate new image
7. Embed metadata in EXIF (UserComment field)

**Cache Invalidation Triggers**:
- Prompt text changes
- Model changes
- Aspect ratio changes
- Reference image changes
- Version bumps

**Reusability**: 100% generic

---

### 3.8 Emotional Annotations

**Location**: `describe_emotional_annotations()` in `nz_trip_daily_itinerary.py`

**Purpose**: Add emotional context to stressful event types for neurodivergent travelers

**Algorithm**:
1. Extract event `kind`, `travel_mode`, `heading`
2. Pattern match to event type:
   - `flight_departure` / `airport_buffer` → airport stress
   - `flight_arrival` → jet lag, immigration
   - `uber` / `drive` → traffic, motion sickness
   - `ferry` → crowding, motion sickness
   - `lodging_*` → coordination, decision fatigue
   - `decision` → paralysis, FOMO
   - Generic → unclear instructions, sensory overload
3. Return tuple: `(triggers, high_point)`

**Example Output**:
- Triggers: "traffic, winding roads, motion sickness, bathroom timing, worrying about arriving late"
- High point: "settling into the drive with scenery/music/conversation"

**Reusability**: 80% generic (framework), 20% custom (specific text descriptions)

---

## 4. Key Abstractions

### 4.1 Domain Model

**Event** - A discrete activity in the itinerary
- Properties: time, location, kind, participants, dependencies
- Types: activity, meal, drive, ferry, flight, lodging, decision
- Constraints: coordination points, hard stops, locked durations

**Venue** - A reusable location with visual/descriptive research
- Persistent across events and trips
- Fuzzy-matchable to events
- Stores AI research artifacts (visual cues, descriptions)

**Itinerary** - Ordered collection of events for a person/group
- Per-person filtering
- Chronological ordering
- Transition generation between events

**Constraint** - Rule limiting itinerary options
- Hard stop: must arrive by deadline
- Coordination point: group must be together
- Dependency: event A must complete before event B

**Slot** - Time block in the itinerary (implicit)
- Defined by event start + duration
- Gaps filled with flexible time or inferred activities

---

### 4.2 Design Patterns

**1. Cache-First Strategy**
- All expensive operations (AI, images, external APIs) are cached
- Fingerprint-based cache keys ensure correctness
- Fail-fast on cache misses (no degraded fallbacks)

**2. Builder Pattern**
- PDF construction uses ReportLab's flowable/frame system
- Incremental assembly of document elements
- Separation of data preparation from rendering

**3. Strategy Pattern**
- Multiple image generation models (Imagen, Gemini Image variants)
- Configurable via environment variables
- Common interface abstracts model differences

**4. Template Method**
- Prompt synthesis follows structured template pattern
- YAML-based prompt configuration
- Placeholder substitution with event context

**5. Repository Pattern**
- Venue lookup module abstracts persistence
- `load_venue()`, `save_venue()`, `find_venue_for_event()`
- Supports migration from cache to persistent docs

**6. Dependency Injection**
- Main orchestrator (`nz_trip_daily_itinerary.py`) imports modules
- No circular dependencies
- Clear module boundaries

**7. Fail-Fast Philosophy**
- No retries, no fallbacks, no best-effort recovery
- Errors surface immediately
- Prevents accumulation of degraded output

---

## 5. Dependencies Between Modules

### 5.1 Module Dependency Graph

```
nz_trip_daily_itinerary.py (Orchestrator)
    ├─→ nz_trip_events_ingest.py (Event parsing)
    ├─→ nz_trip_event_narratives.py (AI content)
    │   ├─→ nz_trip_venue_lookup.py (Venue matching)
    │   └─→ YAML prompt configs
    ├─→ nz_trip_pdf_render.py (PDF layout)
    │   └─→ ReportLab
    ├─→ maps_trip_planner.py (Google Maps API)
    ├─→ weatherspark_typical_weather.py (Weather API)
    └─→ gemini_tone_converter.py (Optional tone conversion)

nz_trip_render.py (High-level wrapper)
    ├─→ nz_trip_events_ingest.py
    ├─→ nz_trip_event_narratives.py
    ├─→ nz_trip_pdf_render.py
    └─→ maps_trip_planner.py

nz_trip_assets.py (Asset pre-generation)
    ├─→ nz_trip_events_ingest.py
    ├─→ nz_trip_event_narratives.py
    ├─→ maps_trip_planner.py
    └─→ weatherspark_typical_weather.py

Venue Management Tools
    nz_trip_venue_list.py
    nz_trip_venue_create.py      All depend on
    nz_trip_venue_enhance.py   → nz_trip_venue_lookup.py
    nz_trip_venue_cleanup.py
    nz_trip_venue_migrate.py
```

### 5.2 External Dependencies

**Python Packages**:
- `google-genai` - Gemini API client
- `requests` - HTTP client for Google Maps, weather APIs
- `reportlab` - PDF generation
- `Pillow` (PIL) - Image processing, EXIF metadata
- `PyYAML` - Prompt configuration parsing
- `python-dateutil` - Date parsing

**External APIs**:
- **Google Gemini API**: Text generation, structured outputs, image generation, search grounding
- **Google Maps Directions API**: Route duration/distance calculation
- **Imagen API** (via Gemini): Day banner image generation
- **WeatherSpark API**: Typical weather data retrieval

---

## 6. Patterns Used

### 6.1 Coding Patterns

**1. Typed Dictionaries**
- Events and venues represented as `Dict[str, Any]`
- Type hints throughout for IDE support
- Runtime validation at boundaries

**2. Pure Functions**
- Most functions are pure (input → output, no side effects)
- Side effects isolated to I/O boundaries (file writes, API calls)
- Makes testing and reasoning easier

**3. Defensive Programming**
- Extensive input validation
- Schema validation for venue documents
- Type checking at runtime boundaries

**4. Configuration as Code**
- YAML files for prompt templates
- Environment variables for runtime config
- Avoids hardcoded magic strings

**5. Logging & Debugging**
- `--verbose` flag for detailed output
- Sidecar files (`.prompt.txt`, `.raw.txt`) for debugging
- EXIF metadata embedding for image tracking

**6. Separation of Concerns**
- Event ingestion ≠ rendering
- Data retrieval ≠ formatting
- AI generation ≠ caching
- Clear module boundaries

---

## 7. NZ-Specific vs Generic/Reusable

### 7.1 NZ-Specific Code

**Hardcoded NZ References**:
- File paths: `new_zealand_trip/`, `nz_trip_venues/`
- Trip dates: Dec 29, 2025 → Jan 10, 2026
- Traveler names: David, Diego, John, Clara, Alex, Stephanie
- Airport codes: SFO, AKL, WLG, ZQN
- NZ place names: Waiheke Island, Rotorua, Taupo, Queenstown, Milford Sound

**NZ-Specific Functions**:
- `_normalize_city_token()` in `nz_trip_event_narratives.py`
  - Maps airport codes to NZ cities
  - Filters out home locations (Mountain View, Menlo Park)

**NZ-Specific Data**:
- Event files: All NZ-specific (wineries, geothermal parks, ferries)
- Venue visual descriptions: NZ architecture, landscape, flora
- Weather locations: NZ cities

---

### 7.2 Generic/Reusable Components

**Fully Generic (Zero Changes Needed)**:

1. **Core Architecture**
   - Event ingestion from Markdown ✓
   - Cache-first AI generation ✓
   - PDF rendering with ReportLab ✓
   - Fingerprint-based cache invalidation ✓
   - Person-specific filtering ✓
   - Chronological event sorting ✓

2. **Modules**:
   - `nz_trip_events_ingest.py` - Generic event parsing
   - `nz_trip_pdf_render.py` - Generic PDF layout (just change theme/fonts)
   - `maps_trip_planner.py` - Generic Google Maps integration
   - `weatherspark_typical_weather.py` - Generic weather API
   - `gemini_tone_converter.py` - Generic Markdown tone conversion

3. **Venue System**:
   - `nz_trip_venue_lookup.py` - Generic venue matching, slug generation, persistence
   - Venue document schema (JSON format)
   - Fuzzy matching algorithm (Jaccard similarity)
   - Schema validation

4. **AI Integration Patterns**:
   - Gemini prompt caching
   - Structured output handling
   - Image generation with fingerprinting
   - YAML-based prompt configuration

5. **Build System**:
   - Makefile-based orchestration
   - Stamp files for dependency tracking
   - Asset pre-generation pattern

---

**Requires Minimal Changes**:

1. **Transition Logic** (`describe_transition_logistics`)
   - Pattern matching is trip-agnostic
   - Would need new patterns for different event types (e.g., train, subway)
   - Core algorithm is generic

2. **Emotional Annotations** (`describe_emotional_annotations`)
   - Event type mapping is generic
   - Specific text descriptions would need updating
   - Pattern is reusable

3. **Prompt Templates** (YAML configs)
   - Structure is generic
   - Content would need updating for different trip types/aesthetics

---

**Would Need Refactoring**:

1. **Hardcoded File Paths**
   - Replace `new_zealand_trip` with `{{trip_name}}`
   - Parameterize venue directory names
   - Configuration file for trip-specific settings

2. **City/Place Normalization**
   - Extract to configuration file
   - Make airport code mapping configurable
   - Support multiple trip contexts

3. **Traveler Names**
   - Move to trip configuration
   - Support dynamic person lists

---

## 8. Edge Cases & Constraints Handled

### 8.1 Time & Scheduling
- Cross-date-line handling (long-haul flights)
- Untimed events
- No-later-than deadlines
- Locked durations (hand-tuned timing)

### 8.2 Group Coordination
- Split groups (different arrival times)
- Coordination points (group must meet)
- Per-person filtering

### 8.3 Travel Logistics
- Multi-modal transport (flight, ferry, rental car, taxi, walking)
- Rental car logistics (pickup, dropoff, multi-car coordination)
- Ferry timing (hard deadlines)

### 8.4 Venue & Location
- Venue disambiguation (same name, different locations)
- Fuzzy matching edge cases
- Address normalization
- Māori characters (macrons)

### 8.5 AI Content Generation
- Prompt truncation handling
- Image quality control (no-text constraints)
- Cache staleness management

### 8.6 PDF Rendering
- Māori macron rendering
- Image scaling ("contain" mode)
- Layout constraints (Letter page size)

### 8.7 Data Integrity
- Event dependencies
- Schema validation
- Inferred vs explicit events

### 8.8 Error Handling
- Fail-fast philosophy (no retries)
- Transition validation
- Cache corruption detection

---

## 9. Recommendations for Extraction

### 9.1 High-Priority Generic Components

**Extract First (Zero NZ Dependencies)**:
1. `nz_trip_events_ingest.py` → `trip_events_ingest.py`
2. `nz_trip_venue_lookup.py` → `trip_venue_system.py`
3. `maps_trip_planner.py` (already generic)
4. `weatherspark_typical_weather.py` (already generic)
5. Core caching utilities (fingerprinting, EXIF metadata)

**Extract with Configuration (Minimal Changes)**:
1. `nz_trip_pdf_render.py` → `trip_pdf_render.py`
   - Parameterize theme/colors
   - Make font choices configurable
2. `nz_trip_event_narratives.py` → `trip_ai_content.py`
   - Extract city normalization to config
   - Make prompt templates external (already YAML)

---

### 9.2 Proposed Generic Architecture

```
itingen/                     # Generic itinerary generator
├── core/
│   ├── events.py           # Event data structures
│   ├── venues.py           # Venue system
│   ├── filtering.py        # Person filtering
│   └── sorting.py          # Chronological sorting
├── integrations/
│   ├── maps.py             # Google Maps API
│   ├── weather.py          # Weather APIs
│   └── ai/
│       ├── gemini.py       # Gemini integration
│       ├── prompts.py      # Prompt management
│       └── caching.py      # Cache strategy
├── rendering/
│   ├── markdown.py         # Markdown generation
│   └── pdf.py              # PDF generation
└── config/
    └── trip_config.py      # Trip-specific settings

trips/                       # Per-trip instances
├── new_zealand_2026/
│   ├── config.yaml
│   ├── events/
│   ├── venues/
│   └── prompts/
└── europe_2027/
    └── ...
```

---

### 9.3 Core Interfaces to Preserve

```python
# Event system
def ingest_events(source: Path) -> List[Event]
def filter_by_person(events: List[Event], person: str) -> List[Event]
def sort_chronologically(events: List[Event]) -> List[Event]

# Venue system
def match_venue(event: Event) -> Optional[Venue]
def load_venue(venue_id: str) -> Venue
def generate_slug(canonical_name: str) -> str

# AI generation
def generate_narrative(event: Event, context: Dict) -> str
def generate_banner_image(date: str, events: List[Event]) -> Image
def generate_thumbnail(event: Event, venue: Optional[Venue]) -> Image

# Rendering
def render_markdown(events: List[Event], person: Optional[str]) -> str
def render_pdf(events: List[Event], person: str, assets: Assets) -> PDF
```

---

### 9.4 Migration Strategy

**Phase 1: Extract Core (No Behavior Changes)**
1. Create new `itingen` package
2. Copy generic modules verbatim
3. Update import paths in NZ trip
4. Verify NZ trip still works

**Phase 2: Parameterize**
1. Introduce `TripConfig` class
2. Replace hardcoded paths with config lookups
3. Extract city/location mappings to config
4. Make traveler lists configurable

**Phase 3: Clean Separation**
1. Move NZ-specific code to `trips/nz_2026/`
2. Generic code stays in `itingen/`
3. Create CLI: `itingen generate --trip nz_2026 --person david`

**Phase 4: Documentation & Testing**
1. Create comprehensive docs
2. Unit tests for generic components
3. Integration tests with sample trip data
4. Example trip configurations

---

## 10. Data Flow Summary

```
INPUT: Per-Day Event Markdown Files
  └→ Event Ingestion (parse Markdown)
      └→ Maps API Enrichment (drive durations)
          └→ Person Filtering (per-person view)
              └→ Chronological Grouping
                  ├→ BRANCH A: Markdown Output
                  │   └→ Write .md files
                  └→ BRANCH B: PDF Generation
                      ├→ AI Content Generation
                      │   ├→ Venue matching
                      │   ├→ Narratives (Gemini)
                      │   ├→ Summaries (Gemini)
                      │   ├→ Taglines (Gemini)
                      │   ├→ Banner images (Imagen)
                      │   └→ Thumbnails (Gemini Image)
                      ├→ External Data
                      │   ├→ Weather (WeatherSpark)
                      │   └→ Venue images
                      └→ PDF Rendering (ReportLab)
                          └→ OUTPUT: Final PDF
```

---

## Conclusion

This system demonstrates **production-quality engineering** with:

✓ **Strong separation of concerns** across 19+ modules
✓ **Robust caching** to minimize API costs and enable iteration
✓ **AI-powered content generation** (narratives, images, summaries)
✓ **Comprehensive edge case handling** (time zones, group splits, multi-modal transport)
✓ **Quality-first philosophy** (fail-fast, no degraded fallbacks)
✓ **~70% generic code** that can be extracted to a reusable library

The core abstractions (Event, Venue, Itinerary, Constraint) are **trip-agnostic**, and the architecture is **well-suited for extraction** into a standalone `itingen` package with per-trip configuration files.

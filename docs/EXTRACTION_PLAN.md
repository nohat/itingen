# Extraction Plan: Generic Itinerary Generator (itingen)

**Plan Status**: Proposed (awaiting approval)
**Created**: 2025-12-29
**Source Project**: `/Users/nohat/scaffold/` (New Zealand Trip System)
**Target**: Generic, reusable trip itinerary generation system

---

## Table of Contents
1. [Extraction Strategy](#1-extraction-strategy)
2. [Proposed File Structure](#2-proposed-file-structure)
3. [What to Extract](#3-what-to-extract)
4. [What to Generalize](#4-what-to-generalize)
5. [What to Rewrite](#5-what-to-rewrite)
6. [What NOT to Extract](#6-what-not-to-extract)
7. [Dependency Order](#7-dependency-order)
8. [Implementation Phases](#8-implementation-phases)
9. [Success Criteria](#9-success-criteria)

---

## 1. Extraction Strategy

### Core Principle
**Extract incrementally, test continuously, generalize ruthlessly**.

### Approach
1. **Start with zero-dependency modules** (utilities, data structures)
2. **Build up the dependency chain** (core → integrations → rendering)
3. **Test each extraction** with NZ trip data
4. **Generalize as we extract** (not after)
5. **Keep the NZ trip working** as validation

### Philosophy Alignment
- ✅ **Simplicity Over Accommodation**: No speculative features, only proven patterns
- ✅ **Explicit Over Implicit**: Configuration files, not magic inference
- ✅ **Fail-Fast**: Clear errors, no silent fallbacks
- ✅ **Test-Driven**: Write tests as we extract

---

## 2. Proposed File Structure

```
itingen/                          # Root project directory
├── .gitignore
├── .claude/                      # Claude Code configuration (already created)
├── README.md
├── pyproject.toml                # Python project config (modern standard)
├── requirements.txt              # Dependencies
├── setup.py                      # Package setup
│
├── itingen/                      # Main package (generic code)
│   ├── __init__.py
│   │
│   ├── core/                     # Core domain logic
│   │   ├── __init__.py
│   │   ├── events.py             # Event data structures & operations
│   │   ├── venues.py             # Venue system
│   │   ├── filtering.py          # Person-specific filtering
│   │   ├── sorting.py            # Chronological sorting
│   │   └── transitions.py        # Transition logic framework
│   │
│   ├── ingest/                   # Data ingestion
│   │   ├── __init__.py
│   │   ├── markdown_parser.py    # Parse event markdown
│   │   └── schema.py             # Data schemas & validation
│   │
│   ├── integrations/             # External service integrations
│   │   ├── __init__.py
│   │   ├── maps/
│   │   │   ├── __init__.py
│   │   │   ├── google_maps.py    # Google Maps API client
│   │   │   └── cache.py          # Maps API caching
│   │   ├── weather/
│   │   │   ├── __init__.py
│   │   │   └── weatherspark.py   # Weather API client
│   │   └── ai/
│   │       ├── __init__.py
│   │       ├── gemini.py         # Gemini API client
│   │       ├── prompts.py        # Prompt loading & templating
│   │       ├── caching.py        # AI content caching (fingerprints)
│   │       └── image_gen.py      # Image generation (banners, thumbs)
│   │
│   ├── rendering/                # Output generation
│   │   ├── __init__.py
│   │   ├── markdown.py           # Markdown itinerary generation
│   │   ├── pdf/
│   │   │   ├── __init__.py
│   │   │   ├── renderer.py       # PDF rendering engine
│   │   │   ├── themes.py         # PDF themes & styling
│   │   │   └── components.py     # Reusable PDF components
│   │   └── assets.py             # Asset pre-generation orchestration
│   │
│   ├── config/                   # Configuration management
│   │   ├── __init__.py
│   │   ├── trip_config.py        # Trip configuration loader
│   │   └── defaults.py           # Default settings
│   │
│   └── utils/                    # Shared utilities
│       ├── __init__.py
│       ├── json_repair.py        # LLM JSON parsing fix (TD-002)
│       ├── slug.py               # Slug generation
│       ├── fingerprint.py        # Cache fingerprinting
│       └── exif.py               # EXIF metadata handling
│
├── trips/                        # Trip-specific instances
│   ├── example/                  # Example trip for documentation
│   │   ├── config.yaml
│   │   ├── events/
│   │   ├── venues/
│   │   └── prompts/
│   └── new_zealand_2026/         # Original NZ trip (validation)
│       ├── config.yaml
│       ├── events/               # Symlink to /Users/nohat/scaffold/.../events
│       ├── venues/               # Symlink to /Users/nohat/scaffold/.../nz_trip_venues
│       └── prompts/              # Symlink to /Users/nohat/scaffold/.../prompt_configs
│
├── tests/                        # Test suite
│   ├── __init__.py
│   ├── conftest.py              # Pytest configuration
│   ├── fixtures/                # Test data
│   ├── unit/                    # Unit tests
│   │   ├── test_events.py
│   │   ├── test_venues.py
│   │   ├── test_sorting.py
│   │   └── ...
│   └── integration/             # Integration tests
│       ├── test_nz_trip.py      # Validate NZ trip still works
│       └── ...
│
├── scripts/                      # CLI tools
│   ├── itingen                   # Main CLI entry point
│   ├── venue_tools.py            # Venue management utilities
│   └── ...
│
└── docs/                         # Documentation (already created)
    ├── ARCHITECTURE.md
    ├── INHERITED_DECISIONS.md
    ├── SOURCE_ANALYSIS.md
    ├── EXTRACTION_PLAN.md        # This file
    ├── TEST_PLAN.md              # Phase 1.4
    └── decisions/
```

---

## 3. What to Extract

### 3.1 Extract Verbatim (100% Reusable)

These modules require **zero changes** - just rename and move:

| Source Module | Target Module | Lines | Notes |
|---------------|---------------|-------|-------|
| `maps_trip_planner.py` | `integrations/maps/google_maps.py` | ~400 | Already generic |
| `weatherspark_typical_weather.py` | `integrations/weather/weatherspark.py` | ~200 | Already generic |
| `gemini_tone_converter.py` | `integrations/ai/tone_converter.py` | ~150 | Already generic |

**Total**: ~750 lines extracted verbatim

---

### 3.2 Extract with Renaming (95% Reusable)

These modules are generic but have NZ-specific names - rename and add minimal configuration:

| Source Module | Target Module | Lines | Changes Needed |
|---------------|---------------|-------|----------------|
| `nz_trip_events_ingest.py` | `ingest/markdown_parser.py` | 294 | Remove `nz_trip` prefix, parameterize paths |
| `nz_trip_venue_lookup.py` | `core/venues.py` | 586 | Remove `nz_trip` prefix, keep all logic |
| `nz_trip_sort_events.py` | `core/sorting.py` | ~100 | Extract sorting logic to function |

**Total**: ~980 lines extracted with minimal changes

---

### 3.3 Extract Core Patterns (80% Reusable)

These modules contain reusable patterns but need refactoring to separate generic from specific:

| Source Module | Target Module | Lines | Refactoring Needed |
|---------------|---------------|-------|-------------------|
| `nz_trip_pdf_render.py` | `rendering/pdf/renderer.py` + `rendering/pdf/themes.py` | 1,400 | Extract theme/styling to config |
| `nz_trip_event_narratives.py` (partial) | `integrations/ai/image_gen.py` + `integrations/ai/caching.py` | 1,500 | Extract caching/fingerprinting utilities |
| `nz_trip_daily_itinerary.py` (partial) | `core/filtering.py` + `core/transitions.py` | 600 | Extract filtering/transition framework |

**Total**: ~3,500 lines to refactor and extract

---

## 4. What to Generalize

### 4.1 Transition Logic

**Source**: `describe_transition_logistics()` in `nz_trip_daily_itinerary.py`

**Current State**: Hardcoded pattern matching with 20+ if/elif branches

**Target State**: Plugin-based transition registry

```python
# core/transitions.py
class TransitionRegistry:
    def __init__(self):
        self._patterns = []

    def register(self, from_kind, to_kind, handler):
        """Register a transition handler for event kind pairs."""
        self._patterns.append((from_kind, to_kind, handler))

    def describe(self, prev_event, curr_event):
        """Find matching handler and generate transition text."""
        for from_kind, to_kind, handler in self._patterns:
            if self._matches(prev_event, from_kind) and self._matches(curr_event, to_kind):
                return handler(prev_event, curr_event)
        raise ValueError(f"No transition handler for {prev_event['kind']} -> {curr_event['kind']}")

# trips/new_zealand_2026/transitions.py
def register_nz_transitions(registry):
    registry.register("drive", "airport_buffer", lambda p, c: f"Drive to {c['location']}...")
    registry.register("ferry", "drive", lambda p, c: f"After the ferry, pick up rental car...")
    # ... NZ-specific patterns
```

**Benefits**:
- Trip-specific transitions stay in trip config
- Generic framework in core
- Extensible for new trip types
- Preserves fail-fast behavior (raises if no match)

---

### 4.2 Emotional Annotations

**Source**: `describe_emotional_annotations()` in `nz_trip_daily_itinerary.py`

**Current State**: Hardcoded text descriptions per event type

**Target State**: Configurable annotation system

```yaml
# trips/new_zealand_2026/config.yaml
emotional_annotations:
  enabled: true
  event_types:
    flight_departure:
      triggers: "security lines, crowds, time pressure, sensory overload"
      high_point: "settling into your seat, knowing the hard part is over"
    drive:
      triggers: "traffic, winding roads, motion sickness, bathroom timing"
      high_point: "settling into the drive with scenery/music/conversation"
```

```python
# core/annotations.py
def generate_annotation(event, config):
    """Generate emotional annotation from config template."""
    annotations = config.get("emotional_annotations", {})
    if not annotations.get("enabled"):
        return None

    event_type_config = annotations["event_types"].get(event["kind"])
    if event_type_config:
        return (event_type_config["triggers"], event_type_config["high_point"])
    return None
```

**Benefits**:
- Opt-in feature (some trips may not need it)
- Customizable per trip
- Generic framework supports any annotation type

---

### 4.3 City/Place Normalization

**Source**: `_normalize_city_token()` in `nz_trip_event_narratives.py`

**Current State**: Hardcoded NZ airport codes and home locations

**Target State**: Trip configuration

```yaml
# trips/new_zealand_2026/config.yaml
locations:
  airport_codes:
    SFO: "San Francisco"
    AKL: "Auckland"
    WLG: "Wellington"
    ZQN: "Queenstown"
  exclude_from_taglines:
    - "Mountain View"
    - "Menlo Park"
    - "San Francisco Bay Area"
```

```python
# integrations/ai/prompts.py
def normalize_city_token(token, config):
    """Normalize city/airport codes using trip config."""
    airport_codes = config.get("locations", {}).get("airport_codes", {})
    return airport_codes.get(token.upper(), token)
```

---

### 4.4 PDF Themes

**Source**: `PdfTheme` class in `nz_trip_pdf_render.py`

**Current State**: Hardcoded Material Design colors, specific fonts

**Target State**: YAML-based theme configuration

```yaml
# trips/new_zealand_2026/theme.yaml
pdf_theme:
  colors:
    primary: "#1976D2"      # Material Blue 700
    on_primary: "#FFFFFF"
    background: "#FAFAFA"   # Material Grey 50
    surface: "#FFFFFF"
  fonts:
    body: "Noto Sans"
    heading: "Noto Sans"
    special_chars: true  # Enable Māori macron support
  spacing:
    padding: 0.75  # inches
    margin_top: 0.72
    margin_bottom: 0.70
  layout:
    page_size: "Letter"
    banner_aspect_ratio: "16:9"
```

```python
# rendering/pdf/themes.py
class PdfTheme:
    @classmethod
    def from_yaml(cls, yaml_path):
        """Load theme from YAML configuration."""
        with open(yaml_path) as f:
            config = yaml.safe_load(f)
        return cls(**config["pdf_theme"])
```

---

## 5. What to Rewrite

### 5.1 Main Orchestrator

**Source**: `nz_trip_daily_itinerary.py` (1,548 lines - monolithic)

**Target**: Modular architecture with clean interfaces

```python
# scripts/itingen (CLI entry point)
"""
Generic CLI for trip itinerary generation.

Usage:
  itingen generate --trip nz_2026 --person david --output pdf
  itingen generate --trip example --format markdown
  itingen venues list --trip nz_2026
  itingen venues create --trip nz_2026
"""

# Rewrite as:
# 1. core/pipeline.py - Main orchestration logic
# 2. config/trip_config.py - Configuration loading
# 3. scripts/itingen - CLI interface
```

**Benefits**:
- Testable orchestration logic (separated from CLI)
- Reusable pipeline for different trip types
- Clear entry point for users

---

### 5.2 Trip Configuration System

**New Module**: `config/trip_config.py`

**Purpose**: Load and validate trip-specific configuration

```python
# config/trip_config.py
from pathlib import Path
from typing import Dict, Any
import yaml

class TripConfig:
    """Load and manage trip-specific configuration."""

    def __init__(self, trip_name: str, trips_dir: Path = None):
        self.trip_name = trip_name
        self.trips_dir = trips_dir or Path("trips")
        self.trip_dir = self.trips_dir / trip_name

        if not self.trip_dir.exists():
            raise ValueError(f"Trip directory not found: {self.trip_dir}")

        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load config.yaml from trip directory."""
        config_path = self.trip_dir / "config.yaml"
        if not config_path.exists():
            raise FileNotFoundError(f"Trip config not found: {config_path}")

        with open(config_path) as f:
            return yaml.safe_load(f)

    def get_events_dir(self) -> Path:
        """Get path to events directory."""
        return self.trip_dir / "events"

    def get_venues_dir(self) -> Path:
        """Get path to venues directory."""
        return self.trip_dir / "venues"

    def get_prompts_dir(self) -> Path:
        """Get path to prompts directory."""
        return self.trip_dir / "prompts"

    def get_travelers(self) -> list:
        """Get list of travelers from config."""
        return self.config.get("travelers", [])

    # ... additional config accessors
```

**Example config.yaml**:
```yaml
# trips/new_zealand_2026/config.yaml
trip:
  name: "New Zealand Adventure 2026"
  start_date: "2025-12-29"
  end_date: "2026-01-10"

travelers:
  - name: "David"
    slug: "david"
  - name: "Diego"
    slug: "diego"
  - name: "John"
    slug: "john"
  - name: "Clara"
    slug: "clara"

locations:
  airport_codes:
    SFO: "San Francisco"
    AKL: "Auckland"
    WLG: "Wellington"
    ZQN: "Queenstown"

integrations:
  google_maps:
    enabled: true
    cache_dir: ".cache/maps"
  weather:
    enabled: true
    provider: "weatherspark"
  ai:
    enabled: true
    provider: "gemini"
    models:
      text: "gemini-2.0-flash-exp"
      image: "imagen-3.0-generate-002"

rendering:
  markdown:
    enabled: true
  pdf:
    enabled: true
    theme: "theme.yaml"

features:
  emotional_annotations: true
  transition_descriptions: true
  ai_summaries: true
```

---

## 6. What NOT to Extract

### 6.1 Gmail Booking Integration
**Source**: TD-012 (rejected)
**Reason**: User-specific workflow, couples to email provider

### 6.2 Dropbox Output Paths
**Source**: TD-016 (rejected)
**Reason**: Hardcoded user filesystem layout

### 6.3 NZ-Specific Event Data
**Reason**: Trip-specific, not part of generic system

### 6.4 Hardcoded Visual Prompts for Specific Venues
**Reason**: Trip-specific venue research, belongs in trip config

### 6.5 NZ-Specific Transition Text
**Reason**: Trip-specific patterns, use plugin system instead

---

## 7. Dependency Order

### Phase 1: Foundation (No Dependencies)
1. ✅ `utils/json_repair.py` - LLM JSON parsing fix
2. ✅ `utils/slug.py` - Slug generation
3. ✅ `utils/fingerprint.py` - Cache fingerprinting
4. ✅ `utils/exif.py` - EXIF metadata handling
5. ✅ `core/events.py` - Event data structures

### Phase 2: Core Logic (Depends on Phase 1)
1. ✅ `core/sorting.py` - Chronological sorting (depends on events)
2. ✅ `core/filtering.py` - Person filtering (depends on events)
3. ✅ `core/venues.py` - Venue system (depends on slug, events)
4. ✅ `ingest/markdown_parser.py` - Event ingestion (depends on events)
5. ✅ `ingest/schema.py` - Schema validation

### Phase 3: External Integrations (Depends on Phase 1-2)
1. ✅ `integrations/maps/google_maps.py` - Maps API (depends on events)
2. ✅ `integrations/weather/weatherspark.py` - Weather API
3. ✅ `integrations/ai/caching.py` - AI caching (depends on fingerprint, exif)
4. ✅ `integrations/ai/prompts.py` - Prompt loading (depends on config)
5. ✅ `integrations/ai/gemini.py` - Gemini client (depends on caching, prompts)
6. ✅ `integrations/ai/image_gen.py` - Image generation (depends on gemini, venues)

### Phase 4: Configuration (Depends on Phase 1-3)
1. ✅ `config/defaults.py` - Default settings
2. ✅ `config/trip_config.py` - Trip config loader

### Phase 5: Rendering (Depends on All Previous)
1. ✅ `rendering/markdown.py` - Markdown generation
2. ✅ `rendering/pdf/components.py` - PDF components
3. ✅ `rendering/pdf/themes.py` - PDF themes (depends on config)
4. ✅ `rendering/pdf/renderer.py` - PDF rendering (depends on themes, components)
5. ✅ `rendering/assets.py` - Asset orchestration

### Phase 6: Orchestration (Depends on All)
1. ✅ `core/transitions.py` - Transition framework (depends on config)
2. ✅ `core/pipeline.py` - Main pipeline orchestration
3. ✅ `scripts/itingen` - CLI entry point

---

## 8. Implementation Phases

### Phase 2.1: Foundation Setup (Week 1)
**Goal**: Set up project structure, extract utilities

**Tasks**:
- [x] Initialize Python package (`pyproject.toml`, `setup.py`)
- [ ] Create directory structure
- [ ] Extract utility modules (json_repair, slug, fingerprint, exif)
- [ ] Write unit tests for utilities
- [ ] Document core data structures (Event, Venue schemas)

**Deliverables**:
- Working `itingen` package skeleton
- 100% test coverage on utilities
- Data structure documentation

---

### Phase 2.2: Core Domain Logic (Week 2)
**Goal**: Extract event/venue management, no external dependencies

**Tasks**:
- [ ] Extract `core/events.py` (Event data structure)
- [ ] Extract `core/sorting.py` (chronological sorting)
- [ ] Extract `core/filtering.py` (person-specific filtering)
- [ ] Extract `core/venues.py` (venue matching, slug generation)
- [ ] Extract `ingest/markdown_parser.py` (event ingestion)
- [ ] Write comprehensive unit tests
- [ ] Add AIDEV-NOTE comments to complex logic

**Deliverables**:
- Core modules with 90%+ test coverage
- Integration test using NZ trip data
- Updated ARCHITECTURE.md

**Validation Criteria**:
- Can ingest NZ trip events
- Can filter by person correctly
- Can match venues with 100% accuracy
- All tests pass

---

### Phase 2.3: External Integrations (Week 3)
**Goal**: Extract API integrations (Maps, Weather, AI)

**Tasks**:
- [ ] Extract `integrations/maps/google_maps.py`
- [ ] Extract `integrations/weather/weatherspark.py`
- [ ] Extract `integrations/ai/caching.py` (fingerprinting, EXIF)
- [ ] Extract `integrations/ai/prompts.py` (YAML loading)
- [ ] Extract `integrations/ai/gemini.py` (Gemini client)
- [ ] Extract `integrations/ai/image_gen.py` (banner/thumbnail generation)
- [ ] Write integration tests (with mocks for API calls)
- [ ] Document API integration patterns

**Deliverables**:
- All integration modules with tests
- Mock fixtures for API responses
- Integration test suite

**Validation Criteria**:
- Can enrich events with Maps API data
- Can fetch weather data
- Can generate AI narratives (with cache hits)
- Can generate images (with cache hits)

---

### Phase 2.4: Configuration System (Week 4)
**Goal**: Implement trip-specific configuration

**Tasks**:
- [ ] Design `config.yaml` schema
- [ ] Implement `config/trip_config.py`
- [ ] Create example trip configuration
- [ ] Implement theme system (PDF, colors, fonts)
- [ ] Implement transition registry
- [ ] Implement annotation system
- [ ] Write config validation tests
- [ ] Document configuration format

**Deliverables**:
- Trip config loader with validation
- Example trip configuration
- Configuration schema documentation

**Validation Criteria**:
- Can load NZ trip config
- Can load example trip config
- Config validation catches errors
- All config accessors work

---

### Phase 2.5: Rendering (Week 5)
**Goal**: Extract Markdown and PDF rendering

**Tasks**:
- [ ] Extract `rendering/markdown.py`
- [ ] Extract `rendering/pdf/components.py` (PDF flowables)
- [ ] Extract `rendering/pdf/themes.py` (theme system)
- [ ] Extract `rendering/pdf/renderer.py` (PDF generation)
- [ ] Extract `rendering/assets.py` (asset orchestration)
- [ ] Generalize transition logic
- [ ] Write rendering tests
- [ ] Document rendering pipeline

**Deliverables**:
- Markdown rendering with tests
- PDF rendering with tests
- Theme customization examples

**Validation Criteria**:
- Can generate Markdown for NZ trip
- Can generate PDF for NZ trip
- PDF matches original quality
- Themes are customizable

---

### Phase 2.6: Orchestration & CLI (Week 6)
**Goal**: Main pipeline and user-facing CLI

**Tasks**:
- [ ] Implement `core/pipeline.py` (orchestration)
- [ ] Implement `scripts/itingen` CLI
- [ ] Implement venue management tools
- [ ] Write end-to-end integration tests
- [ ] Create user documentation
- [ ] Create developer documentation
- [ ] Performance testing

**Deliverables**:
- Working CLI: `itingen generate --trip nz_2026 --person david`
- Venue tools: `itingen venues list`, `itingen venues create`
- Comprehensive documentation
- Performance benchmarks

**Validation Criteria**:
- NZ trip generates correctly via CLI
- Example trip generates correctly
- Performance matches original system
- All documentation complete

---

### Phase 2.7: Polish & Release (Week 7)
**Goal**: Final testing, documentation, cleanup

**Tasks**:
- [ ] Comprehensive testing with NZ trip data
- [ ] Create second example trip (different type - city break or road trip)
- [ ] Write migration guide (how to convert existing trips)
- [ ] Code review and refactoring
- [ ] Performance optimization
- [ ] Documentation review
- [ ] Create release notes

**Deliverables**:
- Production-ready `itingen` package
- Two working example trips
- Migration guide
- Release v0.1.0

**Validation Criteria**:
- NZ trip output matches original 100%
- Example trips generate successfully
- All tests pass
- Documentation is complete
- Performance is acceptable

---

## 9. Success Criteria

### Functional Requirements
- ✅ NZ trip generates identical output (Markdown + PDF)
- ✅ Example trip generates successfully
- ✅ CLI is intuitive and documented
- ✅ Configuration is clear and validated
- ✅ Error messages are helpful

### Technical Requirements
- ✅ Test coverage >= 85%
- ✅ Zero hardcoded NZ-specific logic in core
- ✅ All modules have type hints
- ✅ All complex logic has AIDEV-NOTE comments
- ✅ Performance within 10% of original

### Documentation Requirements
- ✅ README with quick start guide
- ✅ ARCHITECTURE.md updated
- ✅ CONTRIBUTING.md with examples
- ✅ API documentation (docstrings)
- ✅ Configuration schema documented

### Process Requirements
- ✅ All code changes committed after passing tests
- ✅ ADRs written for major decisions
- ✅ Code reviewed before merging
- ✅ Changelog maintained

---

## Next Steps

1. **Get approval** for this extraction plan
2. **Proceed to Phase 1.4**: Identify test cases
3. **Start Phase 2.1**: Foundation setup (pending approval)

---

## Appendix A: File Count Summary

| Category | Source Files | Target Files | Reusability |
|----------|--------------|--------------|-------------|
| Extract Verbatim | 3 | 3 | 100% |
| Extract with Renaming | 3 | 3 | 95% |
| Extract Core Patterns | 3 | 8 | 80% |
| Rewrite | 1 | 3 | N/A |
| **Total** | **10** | **17** | **~85%** |

**Lines of Code**:
- Source: ~12,379 lines
- Estimated Target (generic): ~8,000 lines
- Reduction: ~35% (removing NZ-specific code)

---

## Appendix B: Risk Mitigation

### Risk: Breaking NZ Trip
**Mitigation**: Continuous integration testing against NZ trip data

### Risk: Scope Creep
**Mitigation**: Strict adherence to "extract, don't enhance" principle

### Risk: Over-Generalization
**Mitigation**: Only generalize patterns proven by NZ trip, no speculation

### Risk: Incomplete Extraction
**Mitigation**: Comprehensive test suite validates all functionality

### Risk: Performance Regression
**Mitigation**: Benchmark tests comparing original vs extracted

---

**Plan Status**: Ready for review and approval
**Next**: Phase 1.4 - Identify Test Cases

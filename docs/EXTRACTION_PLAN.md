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

## 2. Proposed File Structure (SPE Model)

```
itingen/                          # Root project directory
├── .gitignore
├── .claude/                      # Claude Code configuration
├── README.md
├── pyproject.toml                # Python project config
├── requirements.txt              # Dependencies
├── setup.py                      # Package setup
│
├── itingen/                      # Main package
│   ├── __init__.py
│   │
│   ├── domain/                   # Pure domain models (No logic)
│   │   ├── __init__.py
│   │   ├── events.py             # Event data structures
│   │   └── venues.py             # Venue data structures
│   │
│   ├── providers/                # The Source (Input)
│   │   ├── __init__.py
│   │   ├── base.py               # BaseProvider interface
│   │   ├── file_provider.py      # Local filesystem provider
│   │   └── markdown_parser.py    # Event parsing logic
│   │
│   ├── pipeline/                 # The Pipeline (Enrichment)
│   │   ├── __init__.py
│   │   ├── orchestrator.py       # Main SPE pipeline runner
│   │   ├── sorting.py            # Chronological sorting
│   │   ├── filtering.py          # Person-specific filtering
│   │   └── transitions.py        # Transition logic
│   │
│   ├── hydrators/                # Pipeline Enrichers
│   │   ├── __init__.py
│   │   ├── base.py               # BaseHydrator interface
│   │   ├── maps.py               # Google Maps enrichment
│   │   ├── weather.py            # Weather enrichment
│   │   └── ai/                   # AI-specific hydration
│   │       ├── __init__.py
│   │       ├── narratives.py     # AI narrative generation
│   │       ├── images.py         # Image generation
│   │       └── cache.py          # AI asset caching
│   │
│   ├── emitters/                 # The Target (Output)
│   │   ├── __init__.py
│   │   ├── base.py               # BaseEmitter interface
│   │   ├── markdown.py           # Markdown publication
│   │   └── pdf/                  # PDF publication
│   │       ├── __init__.py
│   │       ├── renderer.py       # PDF engine
│   │       ├── themes.py         # Theme system
│   │       └── components.py     # Flowable components
│   │
│   ├── config/                   # Global configuration
│   │   ├── __init__.py
│   │   └── defaults.py           # Default settings
│   │
│   └── utils/                    # Shared utilities
│       ├── __init__.py
│       ├── json_repair.py        # LLM JSON fix
│       ├── slug.py               # Slug generation
│       ├── fingerprint.py        # Cache fingerprinting
│       └── exif.py               # EXIF handling
│
├── trips/                        # Trip instances
└── tests/                        # Test suite
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

## 7. Dependency Order (SPE Model)

### Phase 1: Foundation
1. ✅ `utils/json_repair.py`
2. ✅ `utils/slug.py`
3. ✅ `utils/fingerprint.py`
4. ⏳ `utils/exif.py`

### Phase 2: Core SPE Abstractions
1. **`domain/`**: Pure data structures for Events and Venues.
2. **`base.py`**: Interfaces for `BaseProvider`, `BaseHydrator`, `BaseEmitter`.
3. **`pipeline/orchestrator.py`**: Core logic for running the SPE pipeline.

### Phase 3: Providers (The Source)
1. **`providers/file_provider.py`**: Local filesystem implementation.
2. **`providers/markdown_parser.py`**: Event parsing logic.

### Phase 4: Hydrators (The Pipeline)
1. **`pipeline/sorting.py`** & **`pipeline/filtering.py`**.
2. **`hydrators/maps.py`** & **`hydrators/weather.py`**.
3. **`hydrators/ai/`**: Caching and AI enrichment.

### Phase 5: Emitters (The Target)
1. **`emitters/markdown.py`**.
2. **`emitters/pdf/`**: PDF generation system.

### Phase 6: Orchestration & CLI
1. **`scripts/itingen`**: Main entry point.
2. **`pipeline/transitions.py`**: Plugin-based transition registry.

---

## 8. Implementation Phases

### Phase 2.1: Foundation (Utilities)
**Goal**: Finalize extraction of utility modules.

**Tasks**:
- [x] Initialize Python package (`pyproject.toml`, `setup.py`)
- [ ] Create directory structure
- [x] Extract `json_repair.py`, `slug.py`, `fingerprint.py`
- [ ] Extract `exif.py`
- [ ] Write unit tests for all utilities

**Deliverables**:
- Working `itingen` package skeleton
- 100% test coverage on utilities

---

### Phase 2.2: Core SPE Abstractions & Domain Models
**Goal**: Implement the structural foundation of the SPE model.

**Tasks**:
- [ ] Implement `itingen.domain.events` and `itingen.domain.venues` (Pure data structures)
- [ ] Implement `itingen.core.base` (`BaseProvider`, `BaseHydrator`, `BaseEmitter`)
- [ ] Implement `itingen.pipeline.orchestrator` (The SPE runner)
- [ ] Write unit tests for abstractions

**Deliverables**:
- Core SPE interfaces and domain models
- Functional (though empty) pipeline orchestrator

---

### Phase 2.3: Providers (The Source)
**Goal**: Implement data ingestion via the Provider pattern.

**Tasks**:
- [ ] Implement `itingen.providers.file_provider` (Local filesystem support)
- [ ] Implement `itingen.providers.markdown_parser` (Extraction from Markdown)
- [ ] Add config loading logic to `FileProvider`
- [ ] Write unit tests for providers

**Deliverables**:
- Ability to load trip data through a unified `Provider` interface

---

### Phase 2.4: Hydrators (The Pipeline)
**Goal**: Implement enrichment layers as Pipeline Hydrators.

**Tasks**:
- [ ] Implement `itingen.pipeline.sorting` and `itingen.pipeline.filtering`
- [ ] Implement `itingen.hydrators.maps` (Google Maps enrichment)
- [ ] Implement `itingen.hydrators.weather` (WeatherSpark enrichment)
- [ ] Implement `itingen.hydrators.ai` (Gemini narratives, image generation, and caching)
- [ ] Write integration tests for hydrators (with mocks)

**Deliverables**:
- Full enrichment pipeline for event hydration

---

### Phase 2.5: Emitters (The Target)
**Goal**: Implement output generation via the Emitter pattern.

**Tasks**:
- [ ] Implement `itingen.emitters.markdown`
- [ ] Implement `itingen.emitters.pdf.renderer`
- [ ] Implement PDF themes and components
- [ ] Write rendering tests

**Deliverables**:
- Multi-format output generation

---

### Phase 2.6: Orchestration & CLI
**Goal**: Main entry point and final logic wiring.

**Tasks**:
- [ ] Implement `itingen.pipeline.transitions` (Plugin-based registry)
- [ ] Implement `scripts/itingen` CLI
- [ ] Implement venue management tools
- [ ] Write end-to-end integration tests

**Deliverables**:
- Working CLI: `itingen generate --trip nz_2026 --person david`

---

### Phase 2.7: Polish & Release
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

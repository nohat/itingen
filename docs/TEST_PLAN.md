# Test Plan: Generic Itinerary Generator (itingen)

**Plan Status**: Proposed (awaiting approval)
**Created**: 2025-12-29
**Purpose**: Validate extracted generic code and ensure NZ trip functionality is preserved

---

## Table of Contents
1. [Testing Strategy](#1-testing-strategy)
2. [Test Pyramid](#2-test-pyramid)
3. [Unit Tests](#3-unit-tests)
4. [Integration Tests](#4-integration-tests)
5. [End-to-End Tests](#5-end-to-end-tests)
6. [Validation Tests](#6-validation-tests)
7. [Performance Tests](#7-performance-tests)
8. [Test Data](#8-test-data)
9. [Coverage Goals](#9-coverage-goals)

---

## 1. Testing Strategy

### Core Principles
1. **TDD Required**: Write tests BEFORE implementing features
2. **Test at the Right Level**: Unit for logic, integration for APIs, E2E for workflows
3. **NZ Trip as Oracle**: Original NZ trip output is ground truth
4. **Fail-Fast Validation**: Tests must catch regressions immediately
5. **No Mocking Core Logic**: Only mock external APIs (Gemini, Maps, Weather)

### Test Organization
```
tests/
├── unit/              # Fast, isolated, no I/O
├── integration/       # Multiple modules, mocked APIs
├── e2e/               # Full pipeline, real data
├── validation/        # NZ trip regression tests
├── performance/       # Benchmark tests
└── fixtures/          # Shared test data
```

---

## 2. Test Pyramid

```
        /\
       /E2E\           5% - Full pipeline tests
      /----\
     /Valid.\         10% - NZ trip validation
    /--------\
   /Integration\      25% - Multi-module tests
  /------------\
 /  Unit Tests  \     60% - Logic, algorithms
/________________\
```

**Target Breakdown**:
- **Unit**: 60% of tests (~120 tests)
- **Integration**: 25% (~50 tests)
- **Validation**: 10% (~20 tests)
- **E2E**: 5% (~10 tests)

**Total**: ~200 tests minimum

---

## 3. Unit Tests

### 3.1 Utilities (`tests/unit/test_utils.py`)

#### JSON Repair (TD-002)
```python
def test_json_repair_trailing_comma_object():
    """TD-002: Fix trailing comma in JSON object."""
    malformed = '{"key": "value",}'
    repaired = repair_json(malformed)
    assert json.loads(repaired) == {"key": "value"}

def test_json_repair_trailing_comma_array():
    """TD-002: Fix trailing comma in JSON array."""
    malformed = '["a", "b",]'
    repaired = repair_json(malformed)
    assert json.loads(repaired) == ["a", "b"]

def test_json_repair_multiple_trailing_commas():
    """TD-002: Fix multiple trailing commas."""
    malformed = '{"a": [1, 2,], "b": "c",}'
    repaired = repair_json(malformed)
    assert json.loads(repaired) == {"a": [1, 2], "b": "c"}

def test_json_repair_no_change_valid():
    """TD-002: Don't modify valid JSON."""
    valid = '{"key": "value"}'
    repaired = repair_json(valid)
    assert repaired == valid

def test_json_repair_logs_failure():
    """TD-002: Log error on unparseable JSON."""
    invalid = '{"key": "value"'  # Missing closing brace
    with pytest.raises(json.JSONDecodeError):
        repair_json(invalid)
    # Check stderr for error log
```

#### Slug Generation
```python
def test_venue_slug_basic():
    """Generate slug from simple venue name."""
    assert generate_venue_slug("Tantalus Estate (Waiheke Island)") == "tantalus-estate-waiheke"

def test_venue_slug_removes_stopwords():
    """Remove stopwords from venue slug."""
    assert generate_venue_slug("The Vineyard & Winery (Auckland)") == "vineyard-winery-auckland"

def test_venue_slug_handles_special_chars():
    """Handle special characters in venue names."""
    assert generate_venue_slug("Café Māori (Wellington)") == "cafe-maori-wellington"

def test_venue_slug_max_tokens():
    """Respect max_tokens parameter."""
    assert generate_venue_slug("Very Long Venue Name With Many Words", max_tokens=2) == "very-long"

def test_venue_slug_deduplicates_hyphens():
    """Remove duplicate hyphens."""
    assert generate_venue_slug("Estate - - Winery") == "estate-winery"
```

#### Fingerprinting
```python
def test_fingerprint_stable():
    """Fingerprints are stable for identical inputs."""
    payload = {"prompt": "test", "model": "gemini"}
    fp1 = compute_fingerprint(payload)
    fp2 = compute_fingerprint(payload)
    assert fp1 == fp2

def test_fingerprint_changes_on_modification():
    """Fingerprints change when payload changes."""
    payload1 = {"prompt": "test1", "model": "gemini"}
    payload2 = {"prompt": "test2", "model": "gemini"}
    assert compute_fingerprint(payload1) != compute_fingerprint(payload2)

def test_fingerprint_key_order_independent():
    """Fingerprints ignore key order (sorted serialization)."""
    payload1 = {"a": 1, "b": 2}
    payload2 = {"b": 2, "a": 1}
    assert compute_fingerprint(payload1) == compute_fingerprint(payload2)
```

---

### 3.2 Event Core (`tests/unit/test_events.py`)

#### Event Parsing
```python
def test_parse_event_basic_fields():
    """Parse basic event fields from Markdown."""
    markdown = """
## Wine tasting – Tantalus Estate
- time_local: 2025-12-31 11:00
- duration: 1h00m
- kind: activity
- location: Tantalus Estate, Waiheke Island
"""
    event = parse_event_block(markdown)
    assert event["event_heading"] == "Wine tasting – Tantalus Estate"
    assert event["time_local"] == "2025-12-31 11:00"
    assert event["duration"] == "1h00m"
    assert event["kind"] == "activity"

def test_parse_event_list_field():
    """Parse list field (who)."""
    markdown = """
## Test Event
- who: david, diego, john
"""
    event = parse_event_block(markdown)
    assert event["who"] == ["david", "diego", "john"]

def test_parse_event_boolean_field():
    """Parse boolean fields."""
    markdown = """
## Test Event
- coordination_point: true
- hard_stop: false
"""
    event = parse_event_block(markdown)
    assert event["coordination_point"] is True
    assert event["hard_stop"] is False

def test_parse_event_missing_optional():
    """Handle missing optional fields gracefully."""
    markdown = """
## Minimal Event
- time_local: 2025-12-31 11:00
"""
    event = parse_event_block(markdown)
    assert "venue_id" not in event or event.get("venue_id") is None
```

#### Event Sorting (TD-017)
```python
def test_sort_events_by_time_utc():
    """TD-017: Sort events by UTC time for multi-timezone trips."""
    events = [
        {"id": "1", "date": "2025-12-31", "time_utc": "2025-12-31T23:00Z"},
        {"id": "2", "date": "2025-12-31", "time_utc": "2025-12-31T22:00Z"},
    ]
    sorted_events = sort_events_chronologically(events)
    assert [e["id"] for e in sorted_events] == ["2", "1"]

def test_sort_events_untimed_last():
    """Untimed events appear at end of day."""
    events = [
        {"id": "1", "date": "2025-12-31", "time_local": None},
        {"id": "2", "date": "2025-12-31", "time_local": "2025-12-31 14:00"},
    ]
    sorted_events = sort_events_chronologically(events)
    assert [e["id"] for e in sorted_events] == ["2", "1"]

def test_sort_events_fallback_to_no_later_than():
    """Use no_later_than when time_local missing."""
    events = [
        {"id": "1", "date": "2025-12-31", "time_local": None, "no_later_than": "2025-12-31 15:00"},
        {"id": "2", "date": "2025-12-31", "time_local": "2025-12-31 14:00"},
    ]
    sorted_events = sort_events_chronologically(events)
    assert [e["id"] for e in sorted_events] == ["2", "1"]

def test_sort_events_tiebreaker_by_id():
    """Use ID as tiebreaker for same time."""
    events = [
        {"id": "B", "date": "2025-12-31", "time_local": "2025-12-31 14:00"},
        {"id": "A", "date": "2025-12-31", "time_local": "2025-12-31 14:00"},
    ]
    sorted_events = sort_events_chronologically(events)
    assert [e["id"] for e in sorted_events] == ["A", "B"]
```

#### Event Filtering
```python
def test_filter_events_by_person():
    """Filter events for specific person."""
    events = [
        {"id": "1", "who": ["david", "diego"]},
        {"id": "2", "who": ["john", "clara"]},
        {"id": "3", "who": ["david"]},
    ]
    filtered = filter_events_for_person(events, "david")
    assert [e["id"] for e in filtered] == ["1", "3"]

def test_filter_events_group_token():
    """Include events with 'group' token."""
    events = [
        {"id": "1", "who": ["group"]},
        {"id": "2", "who": ["david"]},
    ]
    filtered = filter_events_for_person(events, "john")
    assert [e["id"] for e in filtered] == ["1"]

def test_filter_events_case_insensitive():
    """Person filtering is case-insensitive."""
    events = [
        {"id": "1", "who": ["David", "DIEGO"]},
    ]
    filtered = filter_events_for_person(events, "david")
    assert len(filtered) == 1
```

---

### 3.3 Venue System (`tests/unit/test_venues.py`)

#### Venue Fuzzy Matching
```python
def test_venue_exact_match_by_id():
    """Explicit venue_id match."""
    event = {"venue_id": "tantalus-estate-waiheke"}
    venue = find_venue_for_event(event, venues_dir)
    assert venue["venue_id"] == "tantalus-estate-waiheke"

def test_venue_fuzzy_match_by_name():
    """Fuzzy match by canonical name."""
    event = {"location": "Tantalus Estate, Waiheke Island"}
    venue = find_venue_for_event(event, venues_dir)
    assert venue["canonical_name"] == "Tantalus Estate Vineyard & Winery (Waiheke Island)"

def test_venue_fuzzy_match_by_alias():
    """Fuzzy match by alias."""
    event = {"location": "Tantalus Vineyard"}
    venue = find_venue_for_event(event, venues_dir)
    assert "tantalus" in venue["venue_id"]

def test_venue_fuzzy_match_threshold():
    """Require minimum Jaccard similarity."""
    event = {"location": "Some Random Place"}
    venue = find_venue_for_event(event, venues_dir, threshold=0.8)
    assert venue is None

def test_venue_normalization_removes_addresses():
    """Remove street addresses from matching."""
    event = {"location": "Tantalus Estate, 123 Main St, Waiheke"}
    venue = find_venue_for_event(event, venues_dir)
    assert venue is not None  # Should still match despite address
```

#### Venue Schema Validation
```python
def test_venue_schema_valid():
    """Valid venue passes schema validation."""
    venue = {
        "venue_id": "test-venue",
        "canonical_name": "Test Venue (Test City)",
        "aliases": ["Test"],
        "location": {"region": "Test Region", "country": "Test Country"},
        "metadata": {"created_at": "2025-01-01T00:00:00Z"},
    }
    validate_venue_schema(venue)  # Should not raise

def test_venue_schema_missing_required():
    """Missing required field fails validation."""
    venue = {"canonical_name": "Test Venue"}  # Missing venue_id
    with pytest.raises(SchemaValidationError):
        validate_venue_schema(venue)

def test_venue_schema_invalid_type():
    """Invalid field type fails validation."""
    venue = {
        "venue_id": "test",
        "canonical_name": 123,  # Should be string
    }
    with pytest.raises(SchemaValidationError):
        validate_venue_schema(venue)
```

---

### 3.4 Configuration (`tests/unit/test_config.py`)

```python
def test_trip_config_load():
    """Load trip configuration from YAML."""
    config = TripConfig("example")
    assert config.trip_name == "example"
    assert config.config["trip"]["name"] is not None

def test_trip_config_missing_directory():
    """Raise error if trip directory doesn't exist."""
    with pytest.raises(ValueError):
        TripConfig("nonexistent")

def test_trip_config_missing_yaml():
    """Raise error if config.yaml doesn't exist."""
    # Create empty trip directory without config.yaml
    with pytest.raises(FileNotFoundError):
        TripConfig("empty_trip")

def test_trip_config_get_travelers():
    """Get travelers from config."""
    config = TripConfig("example")
    travelers = config.get_travelers()
    assert len(travelers) > 0
    assert all("name" in t and "slug" in t for t in travelers)

def test_trip_config_get_directories():
    """Get trip directories (events, venues, prompts)."""
    config = TripConfig("example")
    assert config.get_events_dir().exists()
    assert config.get_venues_dir().exists()
    assert config.get_prompts_dir().exists()
```

---

## 4. Integration Tests

### 4.1 Maps API Integration (`tests/integration/test_maps.py`)

```python
@pytest.fixture
def mock_google_maps():
    """Mock Google Maps API responses."""
    with patch("googlemaps.Client") as mock:
        yield mock

def test_maps_enrichment_with_cache_hit(mock_google_maps):
    """Use cached route, don't call API."""
    event = {
        "kind": "drive",
        "travel_from": "A",
        "travel_to": "B",
        "time_local": "2025-12-31 10:00",
    }
    # Pre-populate cache
    save_route_to_cache("A", "B", "drive", "2025-12-31 10:00", 3600, "1 hour")

    enriched = enrich_event_with_maps(event)

    assert enriched["duration_seconds"] == 3600
    assert enriched["duration_text"] == "1 hour"
    mock_google_maps.assert_not_called()  # Cache hit

def test_maps_enrichment_with_cache_miss(mock_google_maps):
    """Call API on cache miss, save to cache."""
    mock_google_maps.return_value.directions.return_value = [{
        "legs": [{"duration": {"value": 3600, "text": "1 hour"}}]
    }]

    event = {
        "kind": "drive",
        "travel_from": "A",
        "travel_to": "B",
        "time_local": "2025-12-31 10:00",
    }

    enriched = enrich_event_with_maps(event)

    assert enriched["duration_seconds"] == 3600
    mock_google_maps.return_value.directions.assert_called_once()

def test_maps_skip_locked_duration():
    """Don't enrich events with lock_duration=true."""
    event = {
        "kind": "drive",
        "lock_duration": True,
        "duration_seconds": 1800,
    }

    enriched = enrich_event_with_maps(event)

    assert enriched["duration_seconds"] == 1800  # Unchanged

def test_maps_handle_past_departure_time():
    """TD-013: Omit departure_time for past events."""
    past_event = {
        "kind": "drive",
        "time_local": "2020-01-01 10:00",  # Past date
        "travel_from": "A",
        "travel_to": "B",
    }

    # Should call API without departure_time parameter
    # (Mock and verify API call excludes departure_time)
```

---

### 4.2 AI Integration (`tests/integration/test_ai.py`)

```python
@pytest.fixture
def mock_gemini():
    """Mock Gemini API responses."""
    with patch("google.genai.GenerativeModel") as mock:
        yield mock

def test_generate_narrative_with_cache_hit(mock_gemini):
    """Use cached narrative, don't call API."""
    event = {"id": "test", "description": "Test event"}
    # Pre-populate cache with fingerprint
    save_narrative_to_cache(fingerprint, "Cached narrative")

    narrative = generate_event_narrative(event)

    assert narrative == "Cached narrative"
    mock_gemini.assert_not_called()

def test_generate_narrative_with_cache_miss(mock_gemini):
    """Call API on cache miss, save to cache."""
    mock_gemini.return_value.generate_content.return_value.text = "Generated narrative"

    event = {"id": "test", "description": "Test event"}
    narrative = generate_event_narrative(event)

    assert narrative == "Generated narrative"
    mock_gemini.return_value.generate_content.assert_called_once()

def test_image_generation_with_fingerprint():
    """Image caching uses fingerprint."""
    payload = {"prompt": "test", "model": "imagen"}
    fp = compute_fingerprint(payload)

    # Generate image
    image_path = generate_banner_image(payload)

    # Verify image saved with fingerprint as filename
    assert fp in str(image_path)

def test_image_exif_metadata():
    """Embed metadata in image EXIF."""
    image_path = generate_banner_image(payload)

    # Read EXIF metadata
    metadata = read_exif_metadata(image_path)

    assert "prompt" in metadata
    assert "model" in metadata
    assert "fingerprint" in metadata
```

---

### 4.3 Full Pipeline (`tests/integration/test_pipeline.py`)

```python
def test_pipeline_markdown_generation():
    """Generate Markdown itinerary from events."""
    config = TripConfig("example")
    events = ingest_events(config.get_events_dir())

    markdown = generate_markdown_itinerary(events, person="alice")

    assert "# " in markdown  # Has headings
    assert len(markdown) > 100  # Not empty

def test_pipeline_pdf_generation():
    """Generate PDF from events."""
    config = TripConfig("example")
    events = ingest_events(config.get_events_dir())
    events = enrich_with_ai_content(events, config)

    pdf_path = generate_pdf_itinerary(events, person="alice", config=config)

    assert pdf_path.exists()
    assert pdf_path.suffix == ".pdf"
    assert pdf_path.stat().st_size > 1000  # Not empty

def test_pipeline_person_filtering():
    """Pipeline correctly filters events by person."""
    config = TripConfig("example")
    events = ingest_events(config.get_events_dir())

    markdown_alice = generate_markdown_itinerary(events, person="alice")
    markdown_bob = generate_markdown_itinerary(events, person="bob")

    assert markdown_alice != markdown_bob  # Different content
```

---

## 5. End-to-End Tests

### 5.1 CLI Tests (`tests/e2e/test_cli.py`)

```python
def test_cli_generate_markdown():
    """CLI: generate markdown itinerary."""
    result = subprocess.run(
        ["itingen", "generate", "--trip", "example", "--person", "alice", "--format", "markdown"],
        capture_output=True,
    )

    assert result.returncode == 0
    assert "itinerary_alice" in result.stdout.decode()

def test_cli_generate_pdf():
    """CLI: generate PDF itinerary."""
    result = subprocess.run(
        ["itingen", "generate", "--trip", "example", "--person", "alice", "--format", "pdf"],
        capture_output=True,
    )

    assert result.returncode == 0
    # Verify PDF file created

def test_cli_venue_list():
    """CLI: list venues."""
    result = subprocess.run(
        ["itingen", "venues", "list", "--trip", "example"],
        capture_output=True,
    )

    assert result.returncode == 0
    assert "venue" in result.stdout.decode().lower()

def test_cli_invalid_trip():
    """CLI: error on invalid trip name."""
    result = subprocess.run(
        ["itingen", "generate", "--trip", "nonexistent"],
        capture_output=True,
    )

    assert result.returncode != 0
    assert "not found" in result.stderr.decode().lower()
```

---

## 6. Validation Tests

### 6.1 NZ Trip Regression (`tests/validation/test_nz_trip.py`)

**Purpose**: Ensure extracted code generates identical output to original system.

```python
def test_nz_trip_event_count():
    """NZ trip has expected number of events."""
    config = TripConfig("new_zealand_2026")
    events = ingest_events(config.get_events_dir())

    assert len(events) == EXPECTED_EVENT_COUNT  # From original system

def test_nz_trip_venue_matching():
    """NZ trip venues match correctly."""
    config = TripConfig("new_zealand_2026")
    events = ingest_events(config.get_events_dir())

    # Check specific known venue matches
    waiheke_event = next(e for e in events if "Tantalus" in e["event_heading"])
    venue = find_venue_for_event(waiheke_event, config.get_venues_dir())

    assert venue["venue_id"] == "tantalus-estate-waiheke"

def test_nz_trip_chronological_order():
    """NZ trip events are in correct chronological order."""
    config = TripConfig("new_zealand_2026")
    events = ingest_events(config.get_events_dir())
    sorted_events = sort_events_chronologically(events)

    # Verify specific known ordering (flight before ferry before wine tasting, etc.)
    assert sorted_events[0]["kind"] == "flight_departure"  # First event is flight

def test_nz_trip_markdown_matches_original():
    """Generated Markdown matches original output."""
    config = TripConfig("new_zealand_2026")
    events = ingest_events(config.get_events_dir())
    events = enrich_with_maps(events, config)

    markdown = generate_markdown_itinerary(events, person="david")

    # Load original Markdown from scaffold project
    original_markdown = load_original_markdown("david")

    # Normalize for comparison (whitespace, timestamps)
    assert normalize_markdown(markdown) == normalize_markdown(original_markdown)

def test_nz_trip_pdf_matches_original():
    """Generated PDF matches original output (visual comparison)."""
    config = TripConfig("new_zealand_2026")
    # Full pipeline
    pdf_path = generate_full_itinerary("new_zealand_2026", person="david")

    # Load original PDF
    original_pdf_path = Path("/Users/nohat/scaffold/...david.pdf")

    # Compare PDFs (page count, file size within tolerance)
    assert pdf_page_count(pdf_path) == pdf_page_count(original_pdf_path)
    assert abs(pdf_path.stat().st_size - original_pdf_path.stat().st_size) < 50000  # 50KB tolerance
```

---

### 6.2 Example Trip Smoke Tests (`tests/validation/test_example_trip.py`)

```python
def test_example_trip_generates_successfully():
    """Example trip generates without errors."""
    result = subprocess.run(
        ["itingen", "generate", "--trip", "example", "--person", "alice"],
        capture_output=True,
    )

    assert result.returncode == 0

def test_example_trip_has_events():
    """Example trip has valid events."""
    config = TripConfig("example")
    events = ingest_events(config.get_events_dir())

    assert len(events) > 0
    assert all("date" in e for e in events)
```

---

## 7. Performance Tests

### 7.1 Benchmark Tests (`tests/performance/test_benchmarks.py`)

```python
def test_benchmark_event_ingestion():
    """Benchmark: ingest 100 events."""
    config = TripConfig("new_zealand_2026")

    start = time.time()
    events = ingest_events(config.get_events_dir())
    duration = time.time() - start

    assert duration < 1.0  # Should be sub-second

def test_benchmark_venue_matching():
    """Benchmark: match 100 events to venues."""
    config = TripConfig("new_zealand_2026")
    events = ingest_events(config.get_events_dir())

    start = time.time()
    for event in events:
        find_venue_for_event(event, config.get_venues_dir())
    duration = time.time() - start

    assert duration < 5.0  # Should be fast with fuzzy matching

def test_benchmark_pdf_generation():
    """Benchmark: generate PDF."""
    config = TripConfig("new_zealand_2026")
    events = load_enriched_events()  # Pre-loaded with AI content

    start = time.time()
    generate_pdf_itinerary(events, person="david", config=config)
    duration = time.time() - start

    assert duration < 30.0  # PDF generation should be under 30 seconds

def test_cache_hit_performance():
    """Benchmark: AI content with 100% cache hits."""
    config = TripConfig("new_zealand_2026")
    events = load_enriched_events()

    start = time.time()
    # Generate with all cache hits
    enrich_with_ai_content(events, config)
    duration = time.time() - start

    assert duration < 2.0  # Cache hits should be near-instant
```

---

## 8. Test Data

### 8.1 Fixtures (`tests/fixtures/`)

**Events**:
```python
# tests/fixtures/events.py
SIMPLE_EVENT = {
    "id": "2025-12-31T1100-wine-test",
    "event_heading": "Wine tasting",
    "date": "2025-12-31",
    "time_local": "2025-12-31 11:00",
    "kind": "activity",
    "who": ["alice", "bob"],
}

DRIVE_EVENT = {
    "id": "2025-12-31T1000-drive-test",
    "kind": "drive",
    "travel_from": "Hotel",
    "travel_to": "Winery",
    "duration": "30m",
}
```

**Venues**:
```python
# tests/fixtures/venues.py
EXAMPLE_VENUE = {
    "venue_id": "test-venue",
    "canonical_name": "Test Venue (Test City)",
    "aliases": ["Test", "Test Venue"],
    "venue_visual_description": "A test venue description.",
    "metadata": {"created_at": "2025-01-01T00:00:00Z"},
}
```

**Config**:
```yaml
# tests/fixtures/example_config.yaml
trip:
  name: "Example Trip"
  start_date: "2026-01-01"
  end_date: "2026-01-07"

travelers:
  - name: "Alice"
    slug: "alice"
  - name: "Bob"
    slug: "bob"
```

---

## 9. Coverage Goals

### 9.1 Coverage Targets

| Module | Unit Coverage | Integration Coverage | Notes |
|--------|---------------|---------------------|-------|
| `utils/*` | 95%+ | N/A | Pure functions, easy to test |
| `core/*` | 90%+ | 80%+ | Core logic, critical |
| `ingest/*` | 85%+ | 75%+ | Parsing edge cases |
| `integrations/*` | 70%+ | 90%+ | Mock APIs heavily |
| `rendering/*` | 80%+ | 85%+ | Visual validation |
| `config/*` | 90%+ | 80%+ | Config edge cases |
| **Overall** | **85%+** | **80%+** | |

---

### 9.2 Coverage Enforcement

**CI/CD Pipeline**:
```bash
# Run tests with coverage
pytest --cov=itingen --cov-report=term-missing --cov-fail-under=85

# Generate HTML coverage report
pytest --cov=itingen --cov-report=html

# Check for missing tests
coverage report --show-missing
```

**Pre-commit Hook**:
- Run unit tests on every commit
- Block commits if coverage drops below threshold

---

## 10. Test Execution Strategy

### 10.1 TDD Workflow

For each new feature:
1. **RED**: Write failing test
2. **GREEN**: Write minimal code to pass
3. **REFACTOR**: Clean up, ensure tests still pass
4. **COMMIT**: Commit working code with tests

### 10.2 Continuous Testing

```bash
# Watch mode during development
pytest --watch

# Run fast tests only (unit)
pytest tests/unit/

# Run slow tests (integration + E2E)
pytest tests/integration/ tests/e2e/

# Run validation suite (NZ trip)
pytest tests/validation/

# Run all tests
pytest
```

### 10.3 CI/CD Integration

**GitHub Actions Workflow**:
```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - run: pip install -r requirements.txt
      - run: pytest --cov=itingen --cov-fail-under=85
      - run: pytest tests/validation/  # NZ trip regression
```

---

## Summary

**Total Test Cases**: ~200+
**Coverage Target**: 85%+
**TDD Required**: Yes
**Validation**: NZ trip as oracle

**Next Steps**:
1. ✅ Phase 1 complete - awaiting approval
2. Proceed to Phase 2.1: Foundation Setup
3. Implement first test suite (utilities)

---

**Plan Status**: Ready for review and approval

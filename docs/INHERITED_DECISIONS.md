# Inherited Technical Decisions

This document critically evaluates architectural decisions and patterns from the original
scaffold project (`/Users/nohat/scaffold/`). We adopt what serves us, modify what partially
applies, and explicitly reject what doesn't fit our goals.

**Guiding Principle**: Fresh code is an opportunity. Don't inherit complexity that doesn't
earn its keep. When in doubt, start simple and add complexity only when proven necessary.

## Source Documents Reviewed
- [x] TECHNICAL_DECISIONS.md (master file)
- [x] TECHNICAL_DECISION_001.md through TECHNICAL_DECISION_017.md (17 numbered decisions)

**Total Reviewed**: 18 technical decision documents

---

## Decisions to Adopt (with justification)

### TD-001: Shared Asset Architecture
**Source**: TECHNICAL_DECISION_001.md
**Original Context**: Multiple travelers sharing same events led to redundant API costs (Gemini image generation, narratives).

**Why It Applies**: CRITICAL for generic trip itinerary generator
- Dramatically reduces AI API costs for group trips
- Ensures visual consistency across all travelers' itineraries
- Speeds up generation for subsequent travelers (nearly instant cache hits)

**Implementation Notes**:
- Cache keys based on intrinsic event data (exclude person-specific fields)
- Per-person assets (narratives with "Good morning, [Name]") remain separate
- Shared assets: banners, thumbnails, venue research, weather data

**Engineering Principle Alignment**: This is NOT speculative fallback code - it solves a concrete, measured cost problem. Passes the Fallback Test.

---

### TD-002: Robust LLM JSON Parsing
**Source**: TECHNICAL_DECISION_002.md
**Original Context**: Gemini occasionally produces `{"key": "value",}` causing pipeline failures.

**Why It Applies**: CRITICAL - prevents build failures from common LLM formatting error

**Implementation Notes**:
- `_extract_json` utility: `re.sub(r",\s*([\]}])", r"\1", json_str)`
- Wrap `json.loads` in try-except with stderr logging
- Keep repair atomic and focused on observed failure modes (trailing commas only)

**Critical Note**: This is NOT over-engineering. The regex handles ONE specific, frequently-observed error. It does NOT try to fix all possible JSON issues. Exactly aligned with "No speculative fallbacks" principle.

---

### TD-004: Extract Prompts to Config
**Source**: TECHNICAL_DECISION_004.md
**Original Context**: Complex multi-line prompts mixed with Python code made maintenance risky.

**Why It Applies**: HIGHLY RECOMMENDED - improves maintainability

**Implementation Notes**:
- `prompt_configs/` directory with YAML files
- Separate configs for different asset types (narratives, images, etc.)
- Config loader utility pattern
- Version control for prompt iterations

**Specific Benefit**:
- Prompts can be updated/tested without touching Python code
- Reduces risk of syntax errors when editing long strings
- Centralized location for all prompt engineering

---

### TD-006: Explicit Metadata Over Inference
**Source**: TECHNICAL_DECISION_006.md & TECHNICAL_DECISION_015.md
**Original Context**: Inference logic matched "inn" inside "dinner", causing wrong lodging selection.

**Why It Applies**: ARCHITECTURAL PRINCIPLE

**Implementation Notes**:
- Day-level metadata in markdown headers: `- lodging_tonight: Hotel Name`
- Ingest pipeline propagates to all events for that day
- Render logic does direct lookup, no inference

**Specific Benefit**:
- Perfect accuracy vs. brittle heuristics
- Easier to debug (single source of truth)
- Eliminates "magic" behavior that's hard to reason about

**Engineering Principle Alignment**: PERFECT example of "Simplicity Over Accommodation". Delete the clever inference code, use explicit data.

---

### TD-010: Precise Layout Geometry
**Source**: TECHNICAL_DECISION_010.md
**Original Context**: Weather card margins were inconsistent, requiring multiple fix attempts.

**Why It Applies**: YES - IF GENERATING PDFs

**Implementation Notes**:
- Calculate inner width: `width = outer_w - (2 * pad)`
- Column widths sum exactly to inner width
- All padding in one place (the container)
- Zero table-level padding (rely on container)

**Specific Benefit**:
- Predictable, debuggable layout
- One-time calculation vs. iterative trial-and-error
- Centralized padding control

**Critical Lesson**: "Visual perfection vs. time cost" - favor explicit geometry over empirical tweaking.

---

### TD-013: Handle Past Event Times
**Source**: TECHNICAL_DECISION_013.md
**Original Context**: Regenerating itineraries mid-trip caused INVALID_REQUEST for morning events from Google Maps API.

**Why It Applies**: YES - IF USING MAPS API

**Implementation Notes**:
```python
if api_mode == "driving" and departure_time < now_ts:
    departure_time = None  # Get standard duration instead of traffic-aware
```

**Specific Benefit**:
- Prevents build failures during active trips
- Allows historical regeneration of itineraries

**Engineering Principle Alignment**: This IS a concrete use case (regenerating itineraries during trip), NOT speculative. Passes the Fallback Test.

---

### TD-014: Event Kind Consistency
**Source**: TECHNICAL_DECISION_014.md
**Original Decision**: Enforce raw-kind policy for internal logic, friendly-string only at display.

**Why It Applies**: YES - ARCHITECTURAL PATTERN

**Implementation Notes**:
- Internal identifiers stay consistent (underscored: `lodging_checkin`)
- Display transformation only at UI layer (friendly: "Lodging Checkin")
- Prevents lookup table mismatches

**Specific Benefit**: Clean separation of concerns, stable internal APIs

---

### TD-017: Cross-Timezone Chronology
**Source**: TECHNICAL_DECISION_017.md
**Original Context**: Cross-timezone travel days sorted incorrectly by local time strings.

**Why It Applies**: YES - FOR MULTI-TIMEZONE TRIPS

**Implementation Notes**:
- Sort key: `(time_utc, time_local, no_later_than, id)`
- Calculate `suppress_tz` if all events share same timezone
- Require explicit `time_utc` and `timezone` in event data

**Specific Benefit**:
- Correct chronological ordering for international travel
- Cleaner display on single-timezone days
- Accurate timeline for long-haul flights

---

### Master: Core Architecture Patterns
**Source**: TECHNICAL_DECISIONS.md (master file)

**Programming Language: Python**
- INHERIT: Excellent for AI/LLM integration, data processing
- Rationale applies to itingen (API support, prototyping speed)

**Local-First Data Storage**
- INHERIT: Privacy, offline capability, full control
- Hybrid Markdown + SQLite pattern is sound

**Project Structure: Organized Monorepo**
- INHERIT: Clear separation of concerns
- `/tools/`, `/data/`, `/prompt_configs/`, etc.

**Virtual Environment + requirements.txt**
- INHERIT: Standard Python practice

---

## Decisions to Modify

### TD-003: Person-Specific Asset Prioritization
**Source**: TECHNICAL_DECISION_003.md
**Original Decision**: Check for person-specific overrides before falling back to generic assets.

**What We're Changing**: Make override mechanism generic, not hardcoded to "banners"

**Why**: The pattern is sound, but implementation in original was coupled to NZ-specific directory structure.

**Our Approach**:
- Keep the priority pattern: `{date}-{person}.ext` before `{date}.ext`
- Make pattern generic: `{asset_type}/{date}-{person}.{ext}` with fallback to `{asset_type}/{date}.{ext}`
- Support arbitrary asset types via configuration

---

### TD-007: Hybrid Display (Table + AI Summary)
**Source**: TECHNICAL_DECISION_007.md
**Original Decision**: Show structured data table AND concise AI-generated tip.

**What We're Changing**: Make it configurable (not all itineraries need both)

**Why**: Good UX pattern, but generic system should allow simpler layouts when AI cost isn't justified.

**Our Approach**:
- Keep the principle: structured data + brief narrative tip
- Add configuration flag to enable/disable AI summaries
- Allow pure table mode for cost-conscious users

---

### TD-011: Heuristic Extraction for Visual Consistency
**Source**: TECHNICAL_DECISION_011.md
**Original Decision**: Scan event text for specific attributes (vehicle colors) and inject as "pinned facts".

**What We're Changing**: Make heuristics pluggable/configurable, not hardcoded

**Why**: The hardcoded "Mach-E" + "Orange" detection is NZ-specific. Generic system needs extensible mechanism.

**Our Approach**:
- Keep the concept of "pinned facts" for image generation
- Pattern: `pinned_facts` extractor registry with user-defined rules
- Plugin architecture for custom extractors per trip

**Critical Note**: The decision doc itself says "Trade-off: This introduces some hardcoded knowledge". For generic system, this becomes a plugin architecture.

---

## Decisions to REJECT

### TD-005: Weather Narrative Integration
**Source**: TECHNICAL_DECISION_005.md
**Original Decision**: Integrate event narratives into weather selection prompt for activity-aware snapshots.

**Why We Reject It**: HIGHLY SPECIFIC to NZ trip workflow (narratives → weather)

**What We Do Instead**:
- Generic system should support independent weather fetching
- If someone wants this coupling, it should be an optional enhancement, not core architecture
- Creates tight coupling between asset generation stages

**What We Learned**: The PATTERN of "context-aware AI selection" is valuable, but this specific implementation is over-fitted to one use case.

---

### TD-008: Weather Box Layout Precision (Specific Measurements)
**Source**: TECHNICAL_DECISION_008.md
**Original Decision**: Specific column widths for weather table (0.32", 0.62", 0.22", etc.)

**Why We Reject It**: These are empirically-derived measurements for NZ trip PDF design

**What We Do Instead**:
- Inherit the PRINCIPLE (explicit geometry) via TD-010
- Don't inherit the SPECIFIC MEASUREMENTS (not portable)
- Make layout measurements configurable per trip theme

---

### TD-009: NZ Trip Itinerary Logic Refinement
**Source**: TECHNICAL_DECISION_009.md
**Original Decision**: Specific fixes to flight times, layovers, lodging for NZ trip.

**Why We Reject It**: This is data cleanup, not a technical decision

**What We Learned**:
- Importance of "dependency tracking" (`depends_on` field) for event relationships - THAT pattern is valuable
- Data corrections themselves are not architectural patterns to extract

---

### TD-012: Booking Integration via Gmail
**Source**: TECHNICAL_DECISION_012.md
**Original Decision**: Extract booking details from Gmail and update itinerary markdown.

**Why We Reject It**:
- This is a workflow for ONE user managing ONE trip
- Generic system shouldn't assume Gmail integration
- Coupling to email provider is anti-pattern for generic tool

**What We Learned**: The concept of "confirmed data replaces placeholders" is valid, but the mechanism shouldn't be hardcoded to a specific email provider.

---

### TD-016: Output Redirection to Dropbox
**Source**: TECHNICAL_DECISION_016.md
**Original Decision**: Redirect PDF output to Dropbox folder with local fallback.

**Why We Reject It**:
- Hardcoded path: `/Users/nohat/Library/CloudStorage/Dropbox/...`
- Specific to one user's filesystem layout
- Generic system needs configurable output paths

**What We Learned**: Principle of "primary + fallback output locations" is valid, but paths must be configurable.

---

## Engineering Philosophy Alignment

### What the Original System Got Right
1. **Explicit over implicit**: Metadata beats inference ✓
2. **Local-first**: Privacy, resilience, offline capability ✓
3. **Config-driven**: Prompts and settings out of code ✓
4. **Fail fast**: Clear errors over silent recovery ✓
5. **Shared resources**: Cache common assets across users ✓

### What the Original System Over-Engineered
1. **Tight coupling**: Weather → narrative → images pipeline ✗
2. **Hardcoded workflows**: Gmail extraction, Dropbox paths ✗
3. **NZ-specific logic**: Vehicle color heuristics, specific measurements ✗

### The Fallback Test Applied
- **TD-002 (JSON repair)**: ✓ PASSES - trailing commas happen regularly, fix is exercised
- **TD-005 (weather-narrative coupling)**: ✗ FAILS - "might be useful" but adds complexity
- **TD-013 (past departure times)**: ✓ PASSES - regenerating during trip is concrete use case
- **TD-016 (Dropbox output)**: ✗ FAILS - assumes specific user's setup

---

## Critical Lessons for Fresh Start

### Don't Inherit Accumulated Cruft
Just because it's in the original doesn't mean it belongs in the generic version. Be ruthless about rejecting over-fitted patterns.

### Plugins Over Hardcoding
Heuristics, extractors, formatters should be extensible. The generic system provides the framework; specific trips provide the customizations.

### Configuration Over Convention
Paths, API keys, output formats, styling must be configurable. No hardcoded assumptions about filesystem layout or user preferences.

### Test with Multiple Use Cases
NZ trip was ONE use case; generic system needs to handle:
- Road trips (single location, day trips)
- City breaks (walking tours, public transit)
- Multi-country tours (trains, cross-border logistics)
- Adventure travel (hiking, extreme sports)

---

## Summary: Inheritance Matrix

| Decision | Status | Rationale |
|----------|--------|-----------|
| TD-001: Shared Assets | ✅ INHERIT | Solves concrete cost problem |
| TD-002: JSON Parsing | ✅ INHERIT | Handles observed failure mode |
| TD-003: Person-Specific | 🔄 ADAPT | Pattern good, make generic |
| TD-004: Prompts in Config | ✅ INHERIT | Maintainability win |
| TD-005: Weather-Narrative | ❌ REJECT | Over-fitted to one workflow |
| TD-006: Explicit Metadata | ✅ INHERIT | Core architectural principle |
| TD-007: Hybrid Display | 🔄 ADAPT | Make configurable |
| TD-008: Layout Measurements | ❌ REJECT | NZ-specific values |
| TD-009: Data Corrections | ❌ REJECT | Not architectural |
| TD-010: Layout Geometry | ✅ INHERIT | Technique is portable |
| TD-011: Pinned Facts | 🔄 ADAPT | Make pluggable |
| TD-012: Gmail Integration | ❌ REJECT | Hardcoded workflow |
| TD-013: Past Event Times | ✅ INHERIT | Concrete use case |
| TD-014: Kind Consistency | ✅ INHERIT | Clean separation |
| TD-015: Lodging Metadata | ✅ INHERIT | Same as TD-006 |
| TD-016: Dropbox Output | ❌ REJECT | Hardcoded paths |
| TD-017: UTC Sorting | ✅ INHERIT | Multi-timezone support |
| Master: Architecture | ✅ INHERIT | Python, local-first, monorepo |

**Totals**: 9 Inherit | 3 Adapt | 5 Reject

---

## Next Steps

1. **Phase 1.3**: Create extraction plan based on these decisions
2. **Phase 1.4**: Identify test cases to validate inherited patterns
3. **Phase 2**: Implement generic system following this guidance

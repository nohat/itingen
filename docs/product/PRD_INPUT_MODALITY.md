# PRD: Input Modality - Agentic Chat Intake System

**Status**: Ratified  
**Owner**: Product  
**Last Updated**: 2026-01-14

## Executive Summary

This PRD defines the transition from file-based manual input to an **agentic chat-based intake system** for itingen. Users will interact with an AI agent through a web chat interface, uploading travel artifacts (confirmations, screenshots, messages) or connecting external services (Gmail, Calendar). The agent extracts structured data, stores it in a SQLite database, and triggers background enrichment pipelines.

This represents a fundamental shift:
- **From**: Human edits Markdown/YAML files
- **To**: Human chats with AI; AI manages structured data

## User Persona: The Trip Architect

**Name**: Alex  
**Context**: Planning a 2-week international trip with family  
**Pain Points**:
- Travel confirmations scattered across email, texts, and screenshots
- No central place to see the full trip timeline
- Manual entry is tedious and error-prone
- Wants a polished PDF itinerary to share with travelers

**Job to Be Done**: *Transform scattered travel artifacts into a publication-ready itinerary without manual data entry.*

## Revised Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         INTAKE LAYER (Agentic Chat)                             │
│                                                                                 │
│  User uploads PDF/image/text → Agent extracts structured data                   │
│  User connects Gmail/Calendar → Agent searches and imports relevant artifacts   │
│                                                                                 │
│  Tools available to agent:                                                      │
│    • add_flight(...)                                                            │
│    • add_hotel(...)                                                             │
│    • add_event(...)                                                             │
│    • search_gmail(query)                                                        │
│    • search_calendar(date_range)                                                │
└─────────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                      ARTIFACT PROCESSING                                        │
│                                                                                 │
│  Attachment Intake:                                                             │
│    • User uploads file → Store in artifact archive                              │
│    • AI extracts bookings (flights, hotels, activities)                         │
│    • Store extractions with audit trail                                         │
│                                                                                 │
│  Connector Intake:                                                              │
│    • Gmail: Search for confirmations → Extract bookings                         │
│    • Calendar: Import events → Reconcile with existing data                     │
│                                                                                 │
│  Booking → Event Conversion:                                                    │
│    • FlightBooking → 2 events (departure, arrival)                              │
│    • HotelBooking → 1 event (check-in) + duration metadata                      │
│    • ActivityBooking → 1 event (start time + duration)                          │
└─────────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                      DATABASE (SQLite → Cloud DB later)                         │
│                                                                                 │
│  Tables:                                                                        │
│    • trips              (trip metadata)                                         │
│    • travelers          (people on the trip)                                    │
│    • venues             (places to visit - auto-created)                        │
│    • events             (time-bound activities)                                 │
│    • artifacts          (uploaded files, emails, calendar events)               │
│    • extractions        (AI extraction results with audit trail)                │
│    • cost_records       (inference cost tracking)                               │
│    • enrichment_jobs    (background processing queue)                           │
└─────────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                      ENRICHMENT LAYER (Background)                              │
│                                                                                 │
│  Hydrators (async processing):                                                  │
│    • MealInferenceHydrator       - Suggest meal events in gaps                  │
│    • CoordinationPointHydrator   - Mark meetup/split points                     │
│    • LogisticsValidationHydrator - Check for impossible transitions             │
│    • CompletenessHydrator        - Identify missing information                 │
│    • VenueAutoCreationHydrator   - Create venues from event locations           │
│                                                                                 │
│  AI Research Agents:                                                            │
│    • Maps API: Directions, transit options, walking times                       │
│    • Weather: Typical conditions for dates/locations                            │
│    • Restaurant search: Find meal options near events                           │
└─────────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                      RENDERING LAYER (PDF, Markdown, JSON)                      │
│                                                                                 │
│  Emitters pull fully enriched data from database:                               │
│    • PDF with banners, maps, weather                                            │
│    • Markdown for quick review                                                  │
│    • JSON for API access                                                        │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Intake Modalities

### 1. Attachment Intake

**User Flow**:
1. User uploads file (PDF, image, text) in chat
2. Agent acknowledges: "I'll process this confirmation..."
3. Agent uses vision/OCR to extract bookings
4. Agent confirms: "I found 2 flights: ..."
5. User approves or corrects

**Technical Design**:
- Store original file in `artifacts/` directory (timestamped, immutable)
- Run AI extraction (generic prompt, not type-specific)
- Store extraction result with confidence scores
- Create events from bookings
- Link events back to source artifact (audit trail)

**AI Extraction Prompt** (generic, not type-specific):
```
You are analyzing a travel document. Extract any bookings you find:

Document: {artifact_content}

Identify:
- Flights (airline, flight number, departure/arrival airports, times, confirmation number)
- Hotels (name, check-in/check-out dates, address, confirmation number)
- Activities (name, date, time, location, confirmation number)
- Car rentals (company, pickup/return dates, location, confirmation number)

Return structured JSON with all bookings found. If multiple bookings exist, extract all.
If no bookings found, return empty array.
```

### 2. Connector Intake

**Gmail Connector**:
- User grants OAuth access to Gmail
- Agent searches: `from:united.com OR from:airbnb.com subject:confirmation`
- Agent shows results: "I found 5 emails that look like confirmations. Process all?"
- User approves → Agent extracts bookings from emails

**Calendar Connector**:
- User grants OAuth access to Google Calendar
- Agent imports events in date range
- Agent reconciles with existing data (avoid duplicates)
- Agent marks calendar-imported events as "tentative" until confirmed

**Technical Design**:
- OAuth 2.0 flow with refresh tokens (stored encrypted)
- Connector search is scoped to date range (avoid importing entire history)
- Default search: 2 weeks before first event, 2 weeks after last event
- User can override search parameters
- Extraction uses same generic AI prompt as attachments

## Enrichment & Smoothing Layer

### Design Philosophy

**Progressive Disclosure**: Start with raw bookings → incrementally enrich → render when "good enough"

**Background Processing**: Enrichment runs async; user can continue working

**Cost-Aware**: Expensive operations (Maps API, AI inference) run only when needed

### Hydrator Pipeline

Each hydrator is a focused, single-purpose enrichment step:

| Hydrator | Trigger | Input | Output | Cost |
|----------|---------|-------|--------|------|
| **MealInferenceHydrator** | Gap >4 hours | Event timeline | Meal event suggestions | Low (LLM) |
| **CoordinationPointHydrator** | People split/join | Event participants | "Meetup" markers | Low (logic) |
| **LogisticsValidationHydrator** | New event added | Event transitions | Warnings for impossible moves | Medium (Maps API) |
| **CompletenessHydrator** | Manual trigger | Full itinerary | Missing info checklist | Low (logic) |
| **VenueAutoCreationHydrator** | Event added | Event location | Venue record (if missing) | None |

### Gap Analysis & Meal Inference

**Problem**: User adds hotel check-in at 3pm, dinner at 8pm. What about 3pm-8pm?

**Solution**: `MealInferenceHydrator` suggests events for unaccounted time.

**Logic**:
- Find gaps >4 hours between events
- If gap crosses typical meal time (12pm-2pm, 6pm-9pm), suggest meal
- If gap is entire afternoon, suggest "Free time / Explore [location]"
- Suggestions are **tentative** (marked with `is_suggested: true` flag)
- User can accept, reject, or modify

**Open Question** (see UX_DECISIONS.md):
- How aggressive should meal suggestions be?
- Should we suggest generic "Lunch" or research specific restaurants?

## Venue Management (Subordinated)

### Design Change: Venues are Auto-Created

**Old Model**: User manually creates venue registry, references venues in events

**New Model**: Venues are automatically created from event locations

**Rationale**:
- Most events already have location data (hotel address, restaurant name, attraction)
- Extracting location from bookings is easier than requiring separate venue registry
- Venue becomes a derived entity, not a primary input

**Technical Design**:
- When event is added, check if venue exists for location
- If not, create venue automatically (geocode address, store lat/lng)
- Venue gets:
  - Name from event location
  - Address (normalized via Maps API)
  - GPS coordinates
  - Automatically generated slug
- User can later enrich venue details (description, photos, tags)

**Venues are still useful for**:
- Deduplication (multiple events at same restaurant)
- Enrichment (one-time Maps/weather lookup, shared across events)
- Rendering (show venue details in PDF)

## Configuration Schema

### Trip Configuration (`trips` table)

```python
{
    "id": "nz_2026",
    "name": "New Zealand Adventure",
    "start_date": "2026-12-29",
    "end_date": "2027-01-15",
    "timezone": "Pacific/Auckland",
    "travelers": [
        {"name": "David", "role": "adult"},
        {"name": "Sarah", "role": "adult"},
        {"name": "Emma", "role": "child"}
    ],
    "theme": {
        "primary_color": "#2c3e50",
        "accent_color": "#e74c3c",
        "font_family": "Lato"
    },
    "enrichment_settings": {
        "meal_inference_enabled": true,
        "meal_inference_gap_hours": 4,
        "logistics_validation_enabled": true,
        "auto_venue_creation": true
    },
    "cost_tracking": {
        "enabled": true,
        "budget_usd": 5000,
        "alert_threshold_pct": 80
    }
}
```

### Design Smells to Address

**Problem 1: Configuration Sprawl**
- Current system has `config.yaml`, `theme.yaml`, `events.md`, `venues.md`
- Hard to maintain consistency across files
- Solution: Consolidate into database schema with versioning

**Problem 2: Manual Editing**
- Current system requires editing YAML/Markdown by hand
- Error-prone, no validation until generation time
- Solution: All edits via chat interface (agent validates immediately)

**Problem 3: File-Based Storage**
- Hard to query (need to parse files)
- Hard to sync (merge conflicts)
- Solution: SQLite with structured queries

## Observability & Cost Tracking

### Motivation

**Problem**: No visibility into inference costs → bill shock

**Goal**: Track every API call, estimate costs, alert when approaching budget

### Architecture

```python
@track_cost(operation="extract_booking", provider="gemini", model="gemini-2.0-flash-thinking-exp-01-21")
def extract_booking_from_pdf(artifact_id: str, file_content: bytes) -> dict:
    # API call happens here
    response = gemini_client.generate_content(...)
    # Decorator captures tokens and logs to cost_records table
    return response
```

### Cost Record Schema

```python
{
    "id": "cost_record_uuid",
    "timestamp": "2026-01-14T07:30:00Z",
    "trip_id": "nz_2026",
    "event_id": "event_123",  # nullable
    "operation": "extract_booking",
    "provider": "gemini",
    "model": "gemini-2.0-flash-thinking-exp-01-21",
    "input_tokens": 1500,
    "output_tokens": 300,
    "cost_usd": 0.0023,
    "duration_ms": 1200,
    "metadata": {
        "artifact_id": "artifact_456",
        "extraction_confidence": 0.95
    }
}
```

### Aggregation Queries

```sql
-- Total cost for a trip
SELECT SUM(cost_usd) FROM cost_records WHERE trip_id = 'nz_2026';

-- Cost by operation type
SELECT operation, SUM(cost_usd) FROM cost_records WHERE trip_id = 'nz_2026' GROUP BY operation;

-- Cost by provider
SELECT provider, model, SUM(cost_usd) FROM cost_records WHERE trip_id = 'nz_2026' GROUP BY provider, model;

-- Daily burn rate
SELECT DATE(timestamp), SUM(cost_usd) FROM cost_records WHERE trip_id = 'nz_2026' GROUP BY DATE(timestamp);
```

### Dashboard Integration

- Show real-time cost counter in web UI
- Alert when >80% of budget consumed
- Show cost breakdown by operation (extraction, enrichment, rendering)
- Export cost records to CSV for analysis

## Agentic Framework Research

### Requirements

1. **Tool calling**: Agent must be able to call functions (add_event, search_gmail, etc.)
2. **Streaming**: Responses should stream token-by-token (better UX)
3. **Multi-modal**: Support text + images (for attachment processing)
4. **Multiple providers**: Switch between Gemini, Claude, GPT-4 based on cost/quality tradeoffs
5. **Cost tracking**: Hook into provider responses to log token usage

### Framework Evaluation

| Framework | Tool Calling | Streaming | Multi-Modal | Multi-Provider | Cost Tracking | Notes |
|-----------|--------------|-----------|-------------|----------------|---------------|-------|
| **Vercel AI SDK** | ✅ Native | ✅ Native | ✅ Yes | ✅ Unified API | ⚠️ Manual | Abstracts provider differences; good Next.js integration |
| **LangChain** | ✅ Via agents | ✅ Via callbacks | ✅ Yes | ✅ Many providers | ⚠️ Via callbacks | Heavy; lots of abstractions; steeper learning curve |
| **LlamaIndex** | ✅ Via tools | ✅ Via streaming | ✅ Yes | ✅ Yes | ⚠️ Via callbacks | Optimized for RAG; may be overkill |
| **Custom (direct API)** | ⚠️ Manual | ⚠️ Manual | ✅ Yes | ⚠️ Manual | ✅ Full control | Maximum control; most work; harder to switch providers |

### Recommendation: Vercel AI SDK

**Why**:
- Native Next.js integration (we're building a web app)
- Clean API for tool calling (define functions, SDK handles invocation)
- Streaming is first-class (not bolted on)
- Unified provider interface (switch between Gemini/Claude/GPT without code changes)
- Good documentation and community support

**Trade-offs**:
- Cost tracking requires manual instrumentation (wrap provider calls)
- Limited to JavaScript/TypeScript (not Python)
- Less flexibility than direct API calls

**Implementation Example**:

```typescript
import { streamText, tool } from 'ai';
import { gemini } from '@ai-sdk/google';

const result = await streamText({
  model: gemini('gemini-2.0-flash-thinking-exp-01-21'),
  messages: [
    { role: 'user', content: 'Here\'s my flight confirmation [attachment]' }
  ],
  tools: {
    add_flight: tool({
      description: 'Add a flight booking to the itinerary',
      parameters: z.object({
        airline: z.string(),
        flight_number: z.string(),
        departure_airport: z.string(),
        arrival_airport: z.string(),
        departure_time: z.string(),
        arrival_time: z.string(),
      }),
      execute: async (params) => {
        // Store in database
        const flight_id = await db.insert('events', {
          type: 'flight',
          ...params
        });
        return { success: true, flight_id };
      }
    })
  }
});
```

### Model Selection Strategy

| Use Case | Primary Model | Fallback | Rationale |
|----------|---------------|----------|-----------|
| **Booking extraction** | Gemini 2.0 Flash | Claude 3.5 Haiku | Vision + structured output; Gemini is cheaper |
| **Chat conversation** | Claude 3.5 Sonnet | Gemini 2.0 Flash | Claude has better conversational quality |
| **Research agents** | Gemini 2.0 Flash | GPT-4o-mini | Fast + cheap for tool-heavy workloads |
| **Creative content** | Claude 3.5 Sonnet | GPT-4o | Higher quality for narrative generation |

**Cost Optimization**:
- Use caching aggressively (Gemini context caching, prompt caching)
- Batch similar operations (extract 5 emails at once, not 1 by 1)
- Compress prompts (remove unnecessary examples after validation)
- Monitor cost per operation; switch models if one is consistently cheaper

## Success Metrics

### User Success

- **Time to first PDF**: <10 minutes from upload to rendered itinerary
- **Extraction accuracy**: >95% of bookings correctly extracted
- **User corrections**: <3 corrections per 10 events (agent gets it right first time)
- **Adoption**: Users prefer chat over manual Markdown editing (measure via survey)

### Technical Success

- **Cost per trip**: <$5 USD for a 2-week trip (all inference costs)
- **Enrichment latency**: <30 seconds for MapsHydrator on 20 events
- **Uptime**: 99% availability (web app accessible)
- **Error rate**: <1% of API calls fail (with retry logic)

### Deferred Metrics (Future)

- **Proactive suggestions accepted**: % of agent suggestions user accepts
- **Connector usage**: % of trips using Gmail/Calendar vs attachments only
- **Multi-user collaboration**: (not in current scope)

## Open Questions (See UX_DECISIONS.md)

1. **Gap Analysis Default**: Should meal suggestions be on by default?
2. **Meal Inference Aggression**: Generic "Lunch" or specific restaurant research?
3. **Coordination Points**: Auto-detect or require manual tagging?
4. **Venue Creation Confirmation**: Ask user before auto-creating venues?
5. **Enrichment Notifications**: Push notifications when enrichment completes?
6. **Connector Search Defaults**: What should default Gmail search query be?
7. **Attachment Auto-Processing**: Start extraction immediately or wait for user confirmation?
8. **Conflict Resolution**: How to handle duplicate events (calendar vs extracted)?

## Related Documentation

- [North Star Vision](NORTH_STAR.md) - Vision and principles
- [TDD: Database](TDD_DATABASE.md) - Database technical design
- [UX Decisions Log](UX_DECISIONS.md) - Open design questions
- [Architecture](../ARCHITECTURE.md) - System design

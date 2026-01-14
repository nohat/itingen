# UX Decisions Log

Decisions that require user testing and iteration. These are explicitly **not finalized**.

## Process

1. **Document the decision** in this log (ADR-style)
2. **Build with a default** that's safe/conservative
3. **Add feature flag** to toggle behavior
4. **Collect usage data** on how users interact
5. **Review quarterly** and finalize decisions with data

---

## UXD-001: Gap Analysis Default Behavior

**Status**: Open  
**Default**: Warn only (no auto-suggestions)  
**Review After**: 10 trips created

### Context

When user adds events with large time gaps (e.g., 3pm hotel check-in, 8pm dinner), should the system:
- A) Auto-suggest events to fill gaps (e.g., "Explore downtown Auckland")
- B) Show a warning "You have 5 hours unaccounted for"
- C) Do nothing (assume user wants free time)

### Default Implementation

Show warning only:
```
⚠️  Gap detected: 3:00pm - 8:00pm (5 hours)
   Consider adding: [Suggest Activities]
```

### Rationale for Default

- **Less intrusive**: User maintains control
- **Avoids noise**: Not all gaps need events (rest time is valid)
- **Easy to change**: Feature flag `meal_inference_enabled` can enable auto-suggestions

### Data to Collect

- How often users click "Suggest Activities"?
- What % of gaps get manually filled?
- User feedback: Do they want more aggressive suggestions?

### Open Questions

1. Should we differentiate between "rest gaps" (2-3 hours) and "unplanned gaps" (6+ hours)?
2. Should suggestions vary by time of day (afternoon = activity, evening = meal)?
3. Should we learn user preferences over time (e.g., prefer restaurants over museums)?

---

## UXD-002: Meal Inference Aggression

**Status**: Open  
**Default**: Only long gaps (>4 hours)  
**Review After**: 20 meal suggestions observed

### Context

When detecting meal events, should the system:
- A) Always suggest specific restaurants (requires Maps API call, costs money)
- B) Suggest generic "Lunch" placeholder (cheap, but less useful)
- C) Only suggest meals if gap crosses typical meal time (12pm-2pm, 6pm-9pm)

### Default Implementation

Suggest generic meal in gaps >4 hours crossing meal times:
```
Suggested: Lunch at 12:30pm (2 hours)
Location: Near [previous event venue]
```

### Rationale for Default

- **Cost-conscious**: Avoid Maps API calls until user confirms interest
- **Reduces noise**: Don't suggest lunch if itinerary already has one
- **User refinement**: User can say "find restaurants nearby" to upgrade suggestion

### Data to Collect

- What % of meal suggestions get accepted?
- What % get upgraded to specific restaurants?
- What % get deleted (user didn't want meal there)?

### Open Questions

1. Should we suggest meals earlier in the day (breakfast at 9am) or only lunch/dinner?
2. Should we infer cuisine type from trip location (sushi in Japan, tapas in Spain)?
3. Should we learn from past trips (user always has coffee break at 3pm)?

---

## UXD-003: Coordination Point Auto-Detection

**Status**: Open  
**Default**: Manual tagging only  
**Review After**: 5 multi-traveler trips

### Context

When travelers split/join (e.g., "David flies in at 2pm, Sarah already at hotel"), should the system:
- A) Auto-detect coordination points from participant changes
- B) Require explicit "meetup" event
- C) Show warning when participants change without transition event

### Default Implementation

Manual tagging only:
```
User must explicitly add:
- Event type: "Meetup" or "Coordination Point"
- Participants before/after
```

### Rationale for Default

- **Avoids false positives**: Participant changes might not be meetups (e.g., solo activities)
- **Simple to build**: No heuristic logic needed
- **Clear intent**: User explicitly marks important coordination moments

### Data to Collect

- How often do multi-traveler trips have coordination points?
- How often do users forget to mark them (complaints/support requests)?
- Would auto-detection reduce user effort?

### Open Questions

1. Should we show a warning when participants change without explicit coordination?
2. Should coordination points trigger enrichment (e.g., suggest nearby landmarks for meetup)?
3. Should we track "last known location" per traveler to validate meetups are possible?

---

## UXD-004: Venue Creation Confirmation

**Status**: Open  
**Default**: Auto-create silently  
**Review After**: 50 venues auto-created

### Context

When event has location but no matching venue exists, should the system:
- A) Auto-create venue silently
- B) Ask user "Create venue for [restaurant name]?"
- C) Show warning "Venue not found, event won't have location details"

### Default Implementation

Auto-create silently:
```python
if event.location and not venue_exists(event.location):
    venue = create_venue_from_location(event.location)
    event.venue_id = venue.id
```

### Rationale for Default

- **Frictionless**: User doesn't have to think about venue management
- **Reversible**: User can delete duplicate venues later
- **Matches expectation**: Location data should "just work"

### Data to Collect

- How many duplicate venues get created?
- How often do users manually merge/delete venues?
- Do users notice venue duplication?

### Open Questions

1. Should we deduplicate by fuzzy name matching (e.g., "Ostro" vs "Ostro Brasserie")?
2. Should we geocode immediately or lazily (on first use)?
3. Should we show "New venue created: [name]" confirmation in chat?

---

## UXD-005: Enrichment Notifications

**Status**: Open  
**Default**: Inline status only (no push)  
**Review After**: 20 enrichment jobs completed

### Context

When background enrichment completes (e.g., Maps API added directions), should the system:
- A) Push notification (browser, email)
- B) Show inline status in web UI ("Enrichment complete")
- C) Silent update (user discovers next time they view trip)

### Default Implementation

Inline status panel:
```
┌────────────────────────────┐
│   ENRICHMENT STATUS        │
│  ✓ Maps directions (12/12) │
│  ✓ Weather data (7/7)      │
│  Updated 2 minutes ago     │
└────────────────────────────┘
```

### Rationale for Default

- **No permission needed**: No browser notification permission prompt
- **Less intrusive**: User checks when ready
- **Matches workflow**: User is actively planning trip (refreshing page)

### Data to Collect

- How long between enrichment complete and user viewing results?
- Do users refresh page frequently to check status?
- Do users request "notify me when done" feature?

### Open Questions

1. Should long-running enrichment (>30 seconds) trigger notification?
2. Should we email user if enrichment fails (e.g., API error)?
3. Should we show estimated completion time ("~15 seconds remaining")?

---

## UXD-006: Connector Search Defaults

**Status**: Open  
**Default**: 2 weeks before/after trip dates  
**Review After**: 10 connector imports

### Context

When user connects Gmail/Calendar, what time range should we search?
- A) All time (import entire history)
- B) Trip dates only (might miss confirmations sent early)
- C) Extended window (2 weeks before/after trip)
- D) User-specified range (more work for user)

### Default Implementation

Extended window:
```python
search_start = trip.start_date - timedelta(weeks=2)
search_end = trip.end_date + timedelta(weeks=2)
```

### Rationale for Default

- **Catches early bookings**: Hotels/flights often booked months in advance
- **Avoids spam**: Don't import unrelated emails
- **Performant**: Limited time range = faster search

### Data to Collect

- What % of imported artifacts fall outside trip dates?
- How far in advance are bookings typically made?
- Do users manually extend search range?

### Open Questions

1. Should we search different ranges for different artifact types (flights: 6 months, activities: 1 month)?
2. Should we show preview of results before importing?
3. Should we auto-detect "too many results" and narrow search?

---

## UXD-007: Attachment Auto-Processing

**Status**: Open  
**Default**: Process immediately  
**Review After**: 50 attachments uploaded

### Context

When user uploads attachment, should we:
- A) Start AI extraction immediately (fast but consumes API credits)
- B) Show preview, wait for user confirmation (slower but safer)
- C) Queue extraction, process in background (async but delayed)

### Default Implementation

Process immediately:
```
User: [uploads confirmation.pdf]

Agent: Processing your confirmation...
       ⟳ Extracting bookings...
       ✓ Found 2 flights. Add to itinerary?
```

### Rationale for Default

- **Feels responsive**: User sees results immediately
- **Low risk**: Extraction is cheap (<$0.01 per document)
- **Matches expectation**: User uploaded file to process it

### Data to Collect

- What % of extractions get rejected/corrected by user?
- What's average extraction cost per document?
- Do users want to review before processing?

### Open Questions

1. Should we show confidence scores before adding events?
2. Should we batch multiple uploads (user drops 5 PDFs at once)?
3. Should we charge differently for large files (>10MB)?

---

## UXD-008: Conflict Resolution

**Status**: Open  
**Default**: Show both, let user decide  
**Review After**: 10 conflicts detected

### Context

When calendar import finds event that matches existing extracted booking:
- A) Auto-merge (prefer calendar or extraction?)
- B) Show both as separate events
- C) Ask user to resolve conflict
- D) Mark one as "duplicate" but keep both

### Default Implementation

Show both with warning:
```
⚠️  Possible duplicate:
    Event 1: UA6755 SFO→AKL (from confirmation.pdf)
    Event 2: Flight to Auckland (from Google Calendar)
    
    [Merge Events] [Keep Both] [Delete Event 1] [Delete Event 2]
```

### Rationale for Default

- **Avoid data loss**: Keep both until user decides
- **Transparency**: User sees all sources
- **Simple logic**: No complex merging heuristics

### Data to Collect

- How often do duplicates occur?
- Which source do users trust more (extraction vs calendar)?
- Do users prefer auto-merge or manual review?

### Open Questions

1. Should we use fuzzy matching (flight number + date) or exact matching only?
2. Should we learn merge preferences (always prefer calendar over extraction)?
3. Should we auto-merge if confidence is high (>95% match)?

---

## Review Schedule

- **Q1 2026**: Review UXD-001, UXD-002, UXD-007 (most user-impacting)
- **Q2 2026**: Review UXD-003, UXD-004, UXD-005 (secondary features)
- **Q3 2026**: Review UXD-006, UXD-008 (connectors, conflicts)

## Related Documentation

- [PRD: Input Modality](PRD_INPUT_MODALITY.md) - Context for these decisions
- [North Star Vision](NORTH_STAR.md) - Product principles guiding defaults

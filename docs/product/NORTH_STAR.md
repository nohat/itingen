# itingen North Star

## Vision

**itingen** transforms scattered travel artifacts—emails, messages, screenshots, bookings—into polished, publication-ready itineraries through AI-assisted conversation. Users interact with an intelligent chat interface that understands intent, retrieves artifacts from connected services, and progressively builds a complete trip plan.

## North Star Product Shape

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              WEB APPLICATION                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │                         CHAT INTERFACE                                       ││
│  │  User: Here's my Air NZ confirmation [attachment: confirmation.pdf]         ││
│  │                                                                              ││
│  │  Agent: I found 2 flights in this confirmation:                              ││
│  │    • UA6755 SFO→AKL Dec 29, 19:50                                           ││
│  │    • NZ106 AKL→WLG Jan 2, 14:30                                             ││
│  │  Added to your itinerary.                                                    ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                                                                                 │
│  ┌──────────────────────────┐  ┌──────────────────────────────────────────────┐│
│  │     TRIP TIMELINE        │  │           ENRICHMENT STATUS                  ││
│  │  Dec 29: Travel Day      │  │  ✓ 12 events extracted                       ││
│  │  Dec 30: Auckland        │  │  ⟳ Enriching: Maps directions (3/12)         ││
│  │  Dec 31: Waiheke         │  │  ○ Pending: Meal suggestions                 ││
│  └──────────────────────────┘  └──────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Core Principles

| Principle | Rationale |
|-----------|-----------|
| **AI-First Intake** | All input is AI-assisted. Even "manual" entry is a conversation with an agent that understands context. |
| **Cloud-Native** | Web app architecture, cloud inference, cloud storage. Local-first is not a priority. |
| **Cost-Conscious** | No monetization plan yet—personal cash funds development. Optimize for low operational cost; measure everything. |
| **Database-First Storage** | Structured data lives in SQLite (migrating to cloud DB later). No human-editable file formats to maintain. |
| **Progressive Enrichment** | Start with raw artifacts → extract bookings → synthesize events → enrich with research → render documents. |
| **Async-Friendly UX** | Enrichment is background work. Users see progress, can continue working, get notified on completion. |

## Deferred Capabilities (Not in Current Roadmap)

| Capability | Reason for Deferral |
|------------|---------------------|
| **Proactive Artifact Discovery** | Requires more UX design—how do we surface suggestions without being annoying? |
| **Mobile App** | Web-first; mobile comes after web is stable |
| **Real-time Collaboration** | Single-planner use case is primary for now |
| **Offline Mode** | Cloud-native; not prioritizing offline |
| **Cloud Database** | Future research—focus on SQLite for now |

## Related Documentation

- [PRD: Input Modality](PRD_INPUT_MODALITY.md) - Detailed product requirements
- [TDD: Database](TDD_DATABASE.md) - Database technical design
- [UX Decisions](UX_DECISIONS.md) - Open UX decisions requiring user testing

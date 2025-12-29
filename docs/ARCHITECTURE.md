# Architecture Documentation

## System Overview

`itingen` is a generic, modular trip itinerary generation system. It extracts and generalizes patterns from a specific trip (New Zealand 2026) into a reusable framework. The system is designed to be local-first, configuration-driven, and highly integrated with external APIs (Google Maps, WeatherSpark, Gemini AI) while maintaining cost efficiency through aggressive caching and resource sharing.

## Architectural Vision: The SPE Model

To ensure long-term maintainability and extensibility, `itingen` is transitioning towards a **Source-Pipeline-Emitter (SPE)** model. This abstract workflow groups components by their role in the data lifecycle rather than their technical implementation.

### 1. Providers (The Source)
Abstracts the origin of trip data. 
- **Role**: Unifies disparate inputs (Markdown events, YAML configs, Venue registries) into a standardized stream of domain objects.
- **Implementations**: `LocalFileProvider` (current), `RemoteApiProvider` (future).

### 2. Hydrators (The Pipeline)
Abstracts the enrichment of the itinerary.
- **Role**: A middleware-style pipeline where each "Hydrator" performs a specific transformation or enrichment on the event stream.
- **Logic**: Maps, Weather, and AI are treated as Hydrators that "hydrate" raw events with external data.
- **Components**: `MapsHydrator`, `WeatherHydrator`, `AiHydrator`.

### 3. Emitters (The Target)
Abstracts the publication of the finished itinerary.
- **Role**: Takes a fully hydrated itinerary and "emits" it in a specific format.
- **Implementations**: `MarkdownEmitter`, `PdfEmitter`, `JsonEmitter`.

## Core Components (Implementation)

The system is organized into several functional packages:

- **`itingen.core`**: Contains the central domain logic, including event data structures, chronological sorting (UTC-aware), person-specific filtering, and the venue lookup system.
- **`itingen.ingest`**: Handles the ingestion of raw data. This includes parsing event descriptions from Markdown and validating data against defined schemas.
- **`itingen.config`**: Manages trip-specific configurations. It loads `config.yaml` and `theme.yaml` to customize the generation process for different trips.
- **`itingen.integrations`**: Encapsulates external service interactions.
    - `maps`: Google Maps API for distance and duration.
    - `weather`: WeatherSpark for typical weather data.
    - `ai`: Gemini AI for narrative generation, image prompt creation, and content caching.
- **`itingen.rendering`**: Orchestrates the output generation for various formats.
    - `markdown`: Simple text-based itineraries.
    - `pdf`: High-fidelity PDF itineraries using ReportLab with custom themes and components.
- **`itingen.utils`**: Shared utility functions such as JSON repair for LLM outputs, slug generation, and EXIF metadata handling.

## Data Flow (SPE Lifecycle)

The system follows a linear transformation pipeline:

1.  **Source Stage**: `Provider` loads raw data and converts it into a `DomainModel` (Events/Venues).
2.  **Pipeline Stage**: The `DomainModel` passes through a sequence of `Hydrators`.
    -   *Sort/Filter*: Initial structural cleanup.
    -   *Enrichment*: External API calls (Maps, Weather, AI) with aggressive caching.
3.  **Emitter Stage**: The fully hydrated `DomainModel` is passed to one or more `Emitters` for publication.

## Design Decisions

Key architectural decisions are recorded as ADRs in [docs/decisions/](decisions/). Major inherited principles include:

- **Explicit Metadata Over Inference**: Prefer explicit tags in data over brittle heuristics.
- **Shared Asset Architecture**: Cache and share AI assets across travelers in the same trip.
- **Fail-Fast**: Raise explicit errors for missing data or configuration rather than using silent fallbacks.

## Dependencies

- **Data Processing**: Python 3.x, YAML, Pydantic (suggested for schemas).
- **External APIs**: Google Maps Platform, Gemini AI, WeatherSpark.
- **PDF Generation**: ReportLab.
- **Utilities**: `json`, `re`, `hashlib`.

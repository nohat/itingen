# Architecture Documentation

## System Overview

`itingen` is a generic, modular trip itinerary generation system. It extracts and generalizes patterns from a specific trip (New Zealand 2026) into a reusable framework. The system is designed to be local-first, configuration-driven, and highly integrated with external APIs (Google Maps, WeatherSpark, Gemini AI) while maintaining cost efficiency through aggressive caching and resource sharing.

## Core Components

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

## Data Flow

The generation pipeline follows a structured path from raw input to finished itinerary:

1. **Input**:
    - **Trip Config**: YAML file defining travelers, dates, and feature flags.
    - **Event Data**: Markdown files with event details and day-level metadata.
    - **Venue Data**: Registry of locations with metadata (address, coordinates, etc.).
    - **Prompts**: YAML-based templates for AI interactions.

2. **Ingestion & Validation**:
    - Raw Markdown is parsed into a stream of `Event` objects.
    - Data is validated against schemas to ensure consistency.

3. **Core Processing**:
    - Events are sorted chronologically, handling cross-timezone transitions.
    - Person-specific filtering is applied based on the traveler's name/slug.
    - Venues are matched to events using name-based lookups and slug generation.

4. **Enrichment (Asset Generation)**:
    - **Maps Enrichment**: Transit times and distances are added between events.
    - **Weather Enrichment**: Typical weather snapshots are fetched for each location.
    - **AI Enrichment**: Narratives are generated; image prompts are created and executed for banners/thumbnails.
    - **Caching**: All external assets are cached using intrinsic event data (fingerprints) to minimize costs and speed up subsequent runs.

5. **Rendering**:
    - The processed and enriched event stream is passed to the renderers.
    - **Markdown Renderer**: Produces a structured text file.
    - **PDF Renderer**: Combines text, maps, weather cards, and AI-generated images into a themed document.

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

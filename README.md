# Trip Itinerary Generator

A standalone system for generating optimized travel itineraries based on venues, constraints, and preferences.

## Features

- AI-powered banner image generation using Google Gemini Nano Banana Pro
- Google Maps integration for route planning and duration calculation
- PDF and Markdown output formats
- Configurable caching strategies
- Test-driven development with 88% coverage

## Installation

```bash
# Install dependencies
pip install -e .

# For development with additional tools
pip install -e ".[dev]"
```

## Usage

### 1. Set up API Keys

Create a `.env` file from the template:

```bash
cp .env.example .env
```

Edit `.env` with your API keys:

```bash
# Google Gemini API Key (for AI image generation)
# Get yours from: https://ai.google.dev/
GEMINI_API_KEY=your_gemini_api_key_here

# Google Maps API Key (for directions, distance, and duration)
# Get yours from: https://console.cloud.google.com/apis/library
GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here
```

### 2. Generate Itinerary

```bash
# Generate both PDF and Markdown formats
python -m src.itingen.cli generate --trip nz_2026

# Generate with AI banner images (requires GEMINI_API_KEY)
python -m src.itingen.cli generate --trip nz_2026 --pdf-banners

# Generate for specific person
python -m src.itingen.cli generate --trip nz_2026 --person david
```

Output will be saved to `output/trips/[trip_name]/`

## Development

This project uses strict Test-Driven Development (TDD).

### Prerequisites
- Python 3.14+
- Google Gemini API key (for AI features)
- Google Maps API key (for route planning)

### Setup
```bash
# Clone the repository
git clone <repo-url>
cd itingen

# Install dependencies
pip install -e ".[dev]"

# Set up API keys
cp .env.example .env
# Edit .env with your API keys

# Run tests
python -m pytest tests/unit/
```

### TDD Workflow
1. Write a failing test
2. Write minimal code to pass
3. Refactor while green
4. Commit

See [.claude/skills/tdd/SKILL.md](.claude/skills/tdd/SKILL.md) for detailed TDD guidelines.

## Architecture

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for system design documentation.

### Core Data Structures

See [docs/DATA_STRUCTURES.md](docs/DATA_STRUCTURES.md) for detailed documentation of Event and Venue models.

## Contributing

See [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) for guidelines.

## Agent Workspaces

This repository supports parallel Cascade agents using Git worktrees. See [docs/agent-workspaces.md](docs/agent-workspaces.md) for operating procedures.

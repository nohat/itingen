# Trip Itinerary Generator

A standalone system for generating optimized travel itineraries based on venues, constraints, and preferences.

## Features

- **AI-Powered Itineraries**: Generate detailed trip itineraries with AI-enriched narratives and emotional context.
- **Visual Storytelling**: Automatic generation of 1:1 event thumbnails and 16:9 day banners using Google Gemini and Imagen.
- **Multi-Format Export**: Export itineraries to Markdown and professionally styled PDFs.
- **Venue Management**: Integrated system for managing and researching trip venues.

## Installation

```bash
# Clone the repository
git clone <repo-url>
cd itingen

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -e .
```

## Usage

```bash
# Generate an itinerary for the NZ 2026 trip
itingen generate --trip nz_2026 --pdf-banners

# List venues for a trip
itingen venues list --trip nz_2026
```

## Environment Setup

The AI features require a Google API key with access to Gemini and Imagen.

1.  Obtain an API key from the [Google AI Studio](https://aistudio.google.com/).
2.  Set the `GOOGLE_API_KEY` environment variable:

```bash
export GOOGLE_API_KEY='your-api-key-here'
```

Alternatively, you can create a `.env` file in the project root:

```text
GOOGLE_API_KEY=your-api-key-here
```

## Development

This project uses strict Test-Driven Development (TDD).

### Prerequisites
- [To be determined]

### Setup
```bash
# Clone the repository
git clone <repo-url>
cd trip-itinerary-generator

# Install dependencies
[INSTALL_COMMAND]

# Run tests
[TEST_COMMAND]
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

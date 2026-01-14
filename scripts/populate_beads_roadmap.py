#!/usr/bin/env python3
"""
One-off script to populate Beads with roadmap tasks.

Run from repository root:
    python scripts/populate_beads_roadmap.py

This creates all epics and tasks for the ratified product roadmap.
"""

import subprocess
import sys

EPICS = [
    {
        "title": "EPIC: Database Migration",
        "description": "Migrate from file-based storage to SQLite database",
        "priority": 1,
        "tasks": [
            {"title": "Design SQLite schema v1", "priority": 1},
            {"title": "Create migration script from Markdown/JSON to SQLite", "priority": 1},
            {"title": "Implement Database access layer (CRUD operations)", "priority": 1},
            {"title": "Implement artifact storage and indexing", "priority": 2},
            {"title": "Update providers to use database instead of file provider", "priority": 1},
            {"title": "Write migration documentation and runbook", "priority": 2},
        ]
    },
    {
        "title": "EPIC: Observability & Cost Tracking",
        "description": "Add cost tracking and observability for inference costs",
        "priority": 1,
        "tasks": [
            {"title": "Design cost tracking schema and tables", "priority": 1},
            {"title": "Implement @track_cost decorator for API calls", "priority": 1},
            {"title": "Add cost tracking to Gemini client", "priority": 1},
            {"title": "Add cost tracking to Google Maps client", "priority": 2},
            {"title": "Implement cost aggregation queries", "priority": 2},
            {"title": "Add cost summary to CLI output", "priority": 2},
        ]
    },
    {
        "title": "EPIC: Artifact Intake System",
        "description": "Build artifact ingestion pipeline with AI extraction",
        "priority": 2,
        "tasks": [
            {"title": "Design artifact archive storage structure", "priority": 1},
            {"title": "Implement artifact indexing and metadata storage", "priority": 1},
            {"title": "Implement AI extraction for attachments (generic, not type-specific)", "priority": 1},
            {"title": "Create booking-to-event conversion logic", "priority": 1},
            {"title": "Add extraction audit trail", "priority": 2},
            {"title": "Implement Gmail connector (OAuth + API)", "priority": 2},
            {"title": "Implement Google Calendar connector", "priority": 2},
        ]
    },
    {
        "title": "EPIC: Enrichment Pipeline",
        "description": "Background enrichment with async processing",
        "priority": 2,
        "tasks": [
            {"title": "Implement enrichment job queue", "priority": 1},
            {"title": "Implement MealInferenceHydrator", "priority": 2},
            {"title": "Implement CoordinationPointHydrator", "priority": 2},
            {"title": "Implement LogisticsValidationHydrator", "priority": 2},
            {"title": "Implement CompletenessHydrator", "priority": 2},
            {"title": "Implement automatic venue creation on event add", "priority": 1},
            {"title": "Add enrichment progress tracking", "priority": 2},
        ]
    },
    {
        "title": "EPIC: Web Application Foundation",
        "description": "Build web app with agentic chat interface",
        "priority": 3,
        "tasks": [
            {"title": "Research and select agentic framework (Vercel AI SDK vs alternatives)", "priority": 1},
            {"title": "Set up Next.js project structure", "priority": 1},
            {"title": "Implement chat UI with streaming responses", "priority": 2},
            {"title": "Implement file attachment handling in chat", "priority": 2},
            {"title": "Define and implement tool calling interface", "priority": 2},
            {"title": "Implement trip timeline view", "priority": 2},
            {"title": "Implement enrichment status panel", "priority": 2},
            {"title": "Implement cost dashboard", "priority": 3},
        ]
    },
]

def run_bd(args: list[str]) -> bool:
    """Run a bd command and return success status."""
    try:
        result = subprocess.run(
            ["bd"] + args,
            capture_output=True,
            text=True,
            check=True
        )
        print(f"  ✓ {' '.join(args[:3])}...")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  ✗ Failed: {e.stderr}")
        return False

def create_issue(title: str, description: str = "", priority: int = 2) -> str | None:
    """Create a Beads issue and return its ID."""
    args = ["create", title, "-p", str(priority)]
    if description:
        args.extend(["-d", description])
    
    try:
        result = subprocess.run(
            ["bd"] + args,
            capture_output=True,
            text=True,
            check=True
        )
        # Parse issue ID from output (assumes format like "Created issue: itingen-xxx")
        for line in result.stdout.split('\n'):
            if 'itingen-' in line.lower():
                parts = line.split()
                for part in parts:
                    if part.startswith('itingen-'):
                        return part.strip()
        return None
    except subprocess.CalledProcessError as e:
        print(f"  ✗ Failed to create '{title}': {e.stderr}")
        return None

def main():
    print("=" * 60)
    print("Populating Beads with Roadmap Tasks")
    print("=" * 60)
    print()
    
    created_count = 0
    failed_count = 0
    
    for epic in EPICS:
        print(f"\n📦 {epic['title']}")
        print("-" * 40)
        
        # Create epic issue
        epic_id = create_issue(
            epic["title"],
            epic.get("description", ""),
            epic["priority"]
        )
        
        if epic_id:
            created_count += 1
            print(f"  Created epic: {epic_id}")
            
            # Create child tasks
            for task in epic.get("tasks", []):
                task_id = create_issue(
                    task["title"],
                    f"Part of {epic['title']}",
                    task.get("priority", 2)
                )
                
                if task_id:
                    created_count += 1
                    # Add dependency to epic
                    run_bd(["dep", "add", task_id, epic_id])
                else:
                    failed_count += 1
        else:
            failed_count += 1
    
    print()
    print("=" * 60)
    print(f"Complete! Created {created_count} issues, {failed_count} failures")
    print()
    print("Next steps:")
    print("  1. Run 'bd list' to see all issues")
    print("  2. Run 'bd ready' to see unblocked work")
    print("  3. Run 'bd sync' to sync with remote")
    print("=" * 60)

if __name__ == "__main__":
    main()

"""Integration tests for the Pipeline Orchestrator."""

import pytest
import yaml
import json
from pathlib import Path

from itingen.pipeline.orchestrator import PipelineOrchestrator
from itingen.providers.file_provider import LocalFileProvider
from itingen.core.base import BaseHydrator, BaseEmitter
from itingen.core.domain.events import Event


class LoggingHydrator(BaseHydrator[Event]):
    """Simple hydrator that logs what it processes."""
    
    def __init__(self, name: str):
        self.name = name
        self.processed = []
    
    def hydrate(self, items: list[Event]) -> list[Event]:
        self.processed = [(item.event_heading, item.kind) for item in items]
        return items


class CountingEmitter(BaseEmitter[Event]):
    """Emitter that counts events and writes a summary."""
    
    def __init__(self):
        self.last_output_path = None
        self.last_count = 0
    
    def emit(self, itinerary: list[Event], output_path: str) -> bool:
        self.last_output_path = output_path
        self.last_count = len(itinerary)
        
        # Write a simple summary file
        summary = {
            "total_events": len(itinerary),
            "events": [
                {
                    "heading": e.event_heading,
                    "kind": e.kind,
                    "location": e.location
                }
                for e in itinerary
            ]
        }
        
        output_file = Path(f"{output_path}_summary.json")
        # Ensure parent directory exists
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w") as f:
            json.dump(summary, f, indent=2)
        
        return True


@pytest.fixture
def sample_trip_dir(tmp_path):
    """Create a sample trip directory structure."""
    trip_dir = tmp_path / "sample_trip"
    trip_dir.mkdir()
    
    # Create directories
    (trip_dir / "events").mkdir()
    (trip_dir / "venues").mkdir()
    
    # Create config.yaml
    config = {
        "trip": {
            "name": "Sample Trip",
            "start_date": "2025-12-29",
            "end_date": "2025-12-30"
        },
        "travelers": [
            {"name": "Alice", "slug": "alice"},
            {"name": "Bob", "slug": "bob"}
        ]
    }
    with open(trip_dir / "config.yaml", "w") as f:
        yaml.dump(config, f)
    
    # Create event files
    day1_events = """- date: 2025-12-29
- city: Auckland

### Event: Airport Arrival
- kind: flight
- location: AKL Airport
- who: Alice, Bob
- description: Arrive at Auckland airport

### Event: Hotel Check-in
- kind: lodging
- location: Grand Hotel
- who: Alice, Bob
- description: Check into hotel
"""
    
    day2_events = """- date: 2025-12-30
- city: Auckland

### Event: City Tour
- kind: activity
- location: City Center
- who: Alice, Bob
- description: Explore the city
"""
    
    with open(trip_dir / "events" / "2025-12-29.md", "w") as f:
        f.write(day1_events)
    
    with open(trip_dir / "events" / "2025-12-30.md", "w") as f:
        f.write(day2_events)
    
    # Create a venue file
    venue = {
        "venue_id": "grand-hotel",
        "canonical_name": "Grand Hotel Auckland",
        "metadata": {
            "address": "123 Queen St, Auckland",
            "created_at": "2025-12-29T12:00:00Z",
            "updated_at": "2025-12-29T12:00:00Z"
        }
    }
    
    with open(trip_dir / "venues" / "grand-hotel.json", "w") as f:
        json.dump(venue, f)
    
    return trip_dir


def test_full_pipeline_integration(sample_trip_dir, tmp_path):
    """Test the full pipeline with real components."""
    # Setup
    provider = LocalFileProvider(sample_trip_dir)
    hydrator = LoggingHydrator("test")
    emitter = CountingEmitter()
    
    # Create orchestrator
    orchestrator = PipelineOrchestrator(
        provider=provider,
        hydrators=[hydrator],
        emitters=[emitter]
    )
    
    # Execute pipeline
    output_dir = tmp_path / "output"
    result = orchestrator.execute(output_dir=output_dir)
    
    # Verify results
    assert len(result) == 3  # 3 events total
    assert emitter.last_count == 3
    assert emitter.last_output_path == str(output_dir / "output_0")
    
    # Check hydrator processed events
    assert len(hydrator.processed) == 3
    assert ("Airport Arrival", "flight") in hydrator.processed
    assert ("Hotel Check-in", "lodging") in hydrator.processed
    assert ("City Tour", "activity") in hydrator.processed
    
    # Check output file was created
    summary_file = Path(f"{emitter.last_output_path}_summary.json")
    assert summary_file.exists()
    
    with open(summary_file) as f:
        summary = json.load(f)
    
    assert summary["total_events"] == 3
    assert len(summary["events"]) == 3
    assert summary["events"][0]["kind"] == "flight"


def test_pipeline_with_no_hydrators(sample_trip_dir, tmp_path):
    """Test pipeline with no hydrators (provider directly to emitter)."""
    provider = LocalFileProvider(sample_trip_dir)
    emitter = CountingEmitter()
    
    orchestrator = PipelineOrchestrator(
        provider=provider,
        hydrators=[],  # No hydrators
        emitters=[emitter]
    )
    
    result = orchestrator.execute(output_dir=tmp_path)
    
    # Should still work, just passing through raw data
    assert len(result) == 3
    assert emitter.last_count == 3


def test_pipeline_with_multiple_hydrators(sample_trip_dir, tmp_path):
    """Test pipeline with multiple hydrators in sequence."""
    provider = LocalFileProvider(sample_trip_dir)
    hydrator1 = LoggingHydrator("first")
    hydrator2 = LoggingHydrator("second")
    emitter = CountingEmitter()
    
    orchestrator = PipelineOrchestrator(
        provider=provider,
        hydrators=[hydrator1, hydrator2],
        emitters=[emitter]
    )
    
    result = orchestrator.execute(output_dir=tmp_path)
    
    # Both hydrators should have processed the data
    assert len(hydrator1.processed) == 3
    assert len(hydrator2.processed) == 3
    assert hydrator1.processed == hydrator2.processed


def test_pipeline_validation(sample_trip_dir):
    """Test pipeline validation with real components."""
    provider = LocalFileProvider(sample_trip_dir)
    
    # Empty pipeline
    orchestrator = PipelineOrchestrator(provider)
    issues = orchestrator.validate()
    assert "No emitters configured - pipeline will not generate output" in issues
    
    # Complete pipeline
    hydrator = LoggingHydrator("test")
    emitter = CountingEmitter()
    orchestrator.add_hydrator(hydrator).add_emitter(emitter)
    issues = orchestrator.validate()
    assert len(issues) == 0

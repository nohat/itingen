#!/usr/bin/env python3
"""Example usage of the Itingen Pipeline Orchestrator.

This script demonstrates how to use the SPE (Source-Pipeline-Emitter) model
to process trip data through a pipeline of hydrators and generate output.
"""

from pathlib import Path
from itingen import PipelineOrchestrator, LocalFileProvider, Event
from itingen.core.base import BaseHydrator, BaseEmitter


class PrintHydrator(BaseHydrator[Event]):
    """Simple hydrator that prints event details."""
    
    def hydrate(self, items: list[Event]) -> list[Event]:
        print(f"\n=== Processing {len(items)} events ===")
        for i, event in enumerate(items):
            print(f"{i+1}. {event.event_heading} ({event.kind}) at {event.location}")
        return items


class JsonEmitter(BaseEmitter[Event]):
    """Emitter that outputs events as JSON."""
    
    def emit(self, itinerary: list[Event], output_path: str) -> bool:
        import json
        
        output = {
            "total_events": len(itinerary),
            "events": [
                {
                    "heading": e.event_heading,
                    "kind": e.kind,
                    "location": e.location,
                    "who": e.who,
                    "description": e.description
                }
                for e in itinerary
            ]
        }
        
        output_file = Path(f"{output_path}.json")
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, "w") as f:
            json.dump(output, f, indent=2)
        
        print(f"\n✓ Output written to: {output_file}")
        return True


def main():
    """Run the pipeline orchestrator example."""
    # Find the sample trip directory
    trip_dir = Path("trips/example")
    if not trip_dir.exists():
        print(f"Sample trip directory not found: {trip_dir}")
        print("Create a sample trip structure at trips/example/ to run this example.")
        return
    
    # Create the pipeline components
    provider = LocalFileProvider(trip_dir)
    hydrator = PrintHydrator()
    emitter = JsonEmitter()
    
    # Build the orchestrator
    orchestrator = PipelineOrchestrator(
        provider=provider,
        hydrators=[hydrator],
        emitters=[emitter]
    )
    
    # Validate the pipeline
    issues = orchestrator.validate()
    if issues:
        print("Pipeline validation issues:")
        for issue in issues:
            print(f"  - {issue}")
        return
    
    # Execute the pipeline
    print("\n🚀 Starting pipeline execution...")
    try:
        result = orchestrator.execute(output_dir=Path("output"))
        print(f"\n✅ Pipeline completed successfully!")
        print(f"   Processed {len(result)} events")
    except Exception as e:
        print(f"\n❌ Pipeline failed: {e}")


if __name__ == "__main__":
    main()

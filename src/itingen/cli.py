"""Main entry point for the itingen CLI.

AIDEV-NOTE: This CLI orchestrates the SPE (Source-Pipeline-Emitter) model.
It supports generating itineraries and managing venues.
"""

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from itingen.pipeline.orchestrator import PipelineOrchestrator
from itingen.providers import FileProvider
from itingen.pipeline.sorting import ChronologicalSorter
from itingen.pipeline.filtering import PersonFilter
from itingen.rendering.markdown import MarkdownEmitter
from itingen.rendering.pdf.renderer import PDFEmitter


def main(args: Optional[List[str]] = None) -> int:
    """Main entry point for the itingen CLI."""
    if args is None:
        args = sys.argv[1:]

    parser = argparse.ArgumentParser(
        prog="itingen",
        description="Generic trip itinerary generation system.",
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Generate command
    generate_parser = subparsers.add_parser("generate", help="Generate a trip itinerary")
    generate_parser.add_argument("--trip", required=True, help="Name of the trip (directory in trips/)")
    generate_parser.add_argument("--person", help="Filter for a specific person's slug")
    generate_parser.add_argument(
        "--format", 
        choices=["markdown", "pdf", "both"], 
        default="both", 
        help="Output format (default: both)"
    )
    generate_parser.add_argument("--output-dir", type=Path, default=Path("output"), help="Directory to write output files")

    # Venues command
    venues_parser = subparsers.add_parser("venues", help="Manage trip venues")
    venues_subparsers = venues_parser.add_subparsers(dest="subcommand", help="Venue subcommand")
    
    list_venues_parser = venues_subparsers.add_parser("list", help="List all venues for a trip")
    list_venues_parser.add_argument("--trip", required=True, help="Name of the trip")
    
    create_venue_parser = venues_subparsers.add_parser("create", help="Create a new venue for a trip")
    create_venue_parser.add_argument("--trip", required=True, help="Name of the trip")

    parsed_args = parser.parse_args(args)

    if not parsed_args.command:
        parser.print_help()
        return 0

    if parsed_args.command == "generate":
        return _handle_generate(parsed_args)
    elif parsed_args.command == "venues":
        return _handle_venues(parsed_args)

    return 0


def _handle_generate(args: argparse.Namespace) -> int:
    """Handle the 'generate' command."""
    print(f"Generating itinerary for trip: {args.trip}...")
    
    try:
        # Initialize Provider
        # Search for trip in trips/ or use absolute path
        trip_path = Path("trips") / args.trip
        if not trip_path.exists():
             trip_path = Path(args.trip)
             
        provider = FileProvider(trip_dir=trip_path)
        
        # Initialize Orchestrator
        orchestrator = PipelineOrchestrator(provider)
        
        # Add Hydrators
        orchestrator.add_hydrator(ChronologicalSorter())
        if args.person:
            orchestrator.add_hydrator(PersonFilter(person_slug=args.person))
            
        # Add Emitters
        if args.format in ["markdown", "both"]:
            orchestrator.add_emitter(MarkdownEmitter())
        if args.format in ["pdf", "both"]:
            orchestrator.add_emitter(PDFEmitter())
            
        # Validate and Execute
        issues = orchestrator.validate()
        for issue in issues:
            print(f"Warning: {issue}")
            
        output_dir = args.output_dir / args.trip
        if args.person:
            output_dir = output_dir / args.person
            
        orchestrator.execute(output_dir=output_dir)
        print(f"Success! Output written to {output_dir}")
        return 0
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def _handle_venues(args: argparse.Namespace) -> int:
    """Handle the 'venues' command."""
    if args.subcommand == "list":
        print(f"Listing venues for trip: {args.trip}...")
        # TODO: Implement venue listing logic
        print("Feature coming soon.")
        return 0
    elif args.subcommand == "create":
        print(f"Creating venue for trip: {args.trip}...")
        # TODO: Implement venue creation logic
        print("Feature coming soon.")
        return 0
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

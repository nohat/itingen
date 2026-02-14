"""Main entry point for the itingen CLI.

AIDEV-NOTE: This CLI orchestrates the SPE (Source-Pipeline-Emitter) model.
It supports generating itineraries and managing venues.
"""

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from itingen.pipeline.orchestrator import PipelineOrchestrator
from itingen.providers import FileProvider, DatabaseProvider
from itingen.pipeline.sorting import ChronologicalSorter
from itingen.pipeline.filtering import PersonFilter
from itingen.pipeline.timing import WrapUpHydrator
from itingen.pipeline.annotations import EmotionalAnnotationHydrator
from itingen.pipeline.transitions_logic import TransitionHydrator
from itingen.pipeline.nz_transitions import create_nz_transition_registry
from itingen.rendering.markdown import MarkdownEmitter
from itingen.rendering.pdf.renderer import PDFEmitter
from itingen.integrations.ai.gemini import GeminiClient
from itingen.integrations.ai.transition_prompts import TRANSITION_STYLE_TEMPLATE
from itingen.hydrators.ai.banner import BannerImageHydrator
from itingen.hydrators.ai.cache import AiCache
from itingen.hydrators.ai.transitions import GeminiTransitionHydrator

DayBannerGenerator = BannerImageHydrator


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
    generate_parser.add_argument(
        "--provider",
        choices=["file", "db"],
        default="file",
        help="Data provider: 'file' (default) or 'db' for database",
    )
    generate_parser.add_argument(
        "--db-path",
        help="Path to SQLite database (required when --provider db)",
    )
    generate_parser.add_argument(
        "--pdf-banners",
        action="store_true",
        help="Enable AI-generated day banner images in the PDF (requires API key; may incur costs)",
    )
    generate_parser.add_argument(
        "--banner-model",
        choices=["gemini-3-pro-image-preview", "gemini-2.5-flash-image"],
        default="gemini-2.5-flash-image",
        help="Model for banner generation (default: gemini-2.5-flash-image for free tier)",
    )
    generate_parser.add_argument(
        "--ai-transitions",
        action="store_true",
        help="Use AI-powered transition generation via Gemini API (requires API key; may incur costs)",
    )

    # Database commands
    db_parser = subparsers.add_parser("db", help="Database management commands")
    db_subparsers = db_parser.add_subparsers(dest="subcommand", help="Database subcommand")

    db_init_parser = db_subparsers.add_parser("init", help="Initialize a new database")
    db_init_parser.add_argument("--db-path", required=True, help="Path to SQLite database file")

    db_migrate_parser = db_subparsers.add_parser("migrate", help="Migrate a trip from files to database")
    db_migrate_parser.add_argument("--trip-dir", required=True, type=Path, help="Path to trip directory")
    db_migrate_parser.add_argument("--db-path", required=True, help="Path to SQLite database file")

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
    elif parsed_args.command == "db":
        return _handle_db(parsed_args)
    elif parsed_args.command == "venues":
        return _handle_venues(parsed_args)

    return 0


def _handle_generate(args: argparse.Namespace) -> int:
    """Handle the 'generate' command."""
    print(f"Generating itinerary for trip: {args.trip}...")

    try:
        # Initialize Provider
        if args.provider == "db":
            if not args.db_path:
                print("Error: --db-path is required when --provider db", file=sys.stderr)
                return 1
            provider = DatabaseProvider(db_path=args.db_path, trip_id=args.trip)
        else:
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

        # Add Wrap-up timing logic
        orchestrator.add_hydrator(WrapUpHydrator())

        # Add Emotional annotations
        orchestrator.add_hydrator(EmotionalAnnotationHydrator())

        # Add Transition descriptions
        if getattr(args, "ai_transitions", False):
            # Use AI-powered transitions
            gemini_client = GeminiClient()
            output_dir = args.output_dir / args.trip
            if args.person:
                output_dir = output_dir / args.person
            cache_dir = output_dir / ".ai_cache"
            ai_cache = AiCache(cache_dir)

            orchestrator.add_hydrator(
                GeminiTransitionHydrator(
                    client=gemini_client,
                    cache=ai_cache,
                    style_template=TRANSITION_STYLE_TEMPLATE
                )
            )
            print("Using AI-powered transition generation via Gemini API")
        else:
            # Use traditional registry-based transitions
            transition_registry = create_nz_transition_registry()
            orchestrator.add_hydrator(TransitionHydrator(transition_registry))

        # Add Emitters
        if args.format in ["markdown", "both"]:
            orchestrator.add_emitter(MarkdownEmitter())
        if args.format in ["pdf", "both"]:
            banner_generator = None
            if getattr(args, "pdf_banners", False):
                output_dir = args.output_dir / args.trip
                if args.person:
                    output_dir = output_dir / args.person
                cache_dir = output_dir / ".ai_cache"
                client = GeminiClient()
                ai_cache = AiCache(cache_dir)
                banner_generator = DayBannerGenerator(
                    client=client,
                    cache=ai_cache,
                    cache_policy="stable_date",  # Stable during development
                    model=getattr(args, "banner_model", "gemini-2.5-flash-image")
                )

            orchestrator.add_emitter(PDFEmitter(banner_generator=banner_generator))

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


def _handle_db(args: argparse.Namespace) -> int:
    """Handle the 'db' command."""
    if args.subcommand == "init":
        from itingen.db.schema import init_db
        try:
            init_db(args.db_path)
            print(f"Database initialized at {args.db_path}")
            return 0
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

    elif args.subcommand == "migrate":
        from itingen.db.migrate import migrate_trip
        try:
            trip_id = migrate_trip(args.trip_dir, args.db_path)
            print(f"Successfully migrated trip '{trip_id}' to {args.db_path}")
            return 0
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

    else:
        print("Error: specify a subcommand (init, migrate)", file=sys.stderr)
        return 1


def _handle_venues(args: argparse.Namespace) -> int:
    """Handle the 'venues' command."""
    if args.subcommand == "list":
        print(f"Listing venues for trip: {args.trip}...")
        try:
            trip_path = Path("trips") / args.trip
            if not trip_path.exists():
                trip_path = Path(args.trip)

            provider = FileProvider(trip_dir=trip_path)
            venues = provider.get_venues()

            if not venues:
                print("No venues found.")
                return 0

            for venue_id, venue in venues.items():
                print(f"- {venue_id}: {venue.canonical_name} ({venue.address})")
            return 0
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
    elif args.subcommand == "create":
        print(f"Creating venue for trip: {args.trip}...")
        try:
            trip_path = Path("trips") / args.trip
            if not trip_path.exists():
                trip_path = Path(args.trip)

            provider = FileProvider(trip_dir=trip_path)

            # Simple interactive creation
            venue_id = input("Venue ID (slug): ").strip()
            canonical_name = input("Canonical Name: ").strip()
            address = input("Address: ").strip()
            kind = input("Kind: ").strip()

            if not venue_id or not canonical_name:
                print("Error: Venue ID and Canonical Name are required.", file=sys.stderr)
                return 1

            venue_data = {
                "venue_id": venue_id,
                "canonical_name": canonical_name,
                "address": address,
                "kind": kind
            }

            # Ensure venues directory exists
            venues_dir = trip_path / "venues"
            venues_dir.mkdir(parents=True, exist_ok=True)

            venue_file = venues_dir / f"{venue_id}.json"
            import json
            with open(venue_file, "w", encoding="utf-8") as f:
                json.dump(venue_data, f, indent=2)

            print(f"Venue created successfully at {venue_file}")
            return 0
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())

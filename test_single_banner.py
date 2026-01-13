#!/usr/bin/env python3
"""Test script to generate exactly ONE banner image for validation.

This exercises the complete banner generation pipeline from the NZ trip,
generating a banner for 2026-01-02 (middle day of the trip).
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from PIL import Image

# Load environment - override any existing env vars
load_dotenv(override=True)

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from itingen.providers import FileProvider
from itingen.pipeline.orchestrator import PipelineOrchestrator
from itingen.pipeline.sorting import ChronologicalSorter
from itingen.pipeline.timing import WrapUpHydrator
from itingen.pipeline.annotations import EmotionalAnnotationHydrator
from itingen.pipeline.transitions_logic import TransitionHydrator
from itingen.rendering.timeline import TimelineProcessor
from itingen.integrations.ai.gemini import GeminiClient
from itingen.hydrators.ai.banner import BannerImageHydrator
from itingen.hydrators.ai.cache import AiCache


def main():
    """Generate one banner image for the middle day of NZ trip."""
    print("=" * 70)
    print("Testing Banner Generation Pipeline")
    print("=" * 70)
    print()

    # Check API key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY not found in .env")
        return 1
    print(f"✓ API Key loaded: {api_key[:20]}...")
    print()

    # Setup trip
    trip_path = Path("trips/nz_2026")
    if not trip_path.exists():
        print(f"ERROR: Trip directory not found: {trip_path}")
        return 1
    print(f"✓ Trip directory: {trip_path}")
    print()

    # Initialize Provider
    provider = FileProvider(trip_dir=trip_path)

    # Initialize Orchestrator with full pipeline
    print("Setting up pipeline...")
    orchestrator = PipelineOrchestrator(provider)
    orchestrator.add_hydrator(ChronologicalSorter())
    orchestrator.add_hydrator(WrapUpHydrator())
    orchestrator.add_hydrator(EmotionalAnnotationHydrator())
    orchestrator.add_hydrator(TransitionHydrator())
    print("✓ Pipeline configured")
    print()

    # Load and process events
    print("Loading and processing events...")
    events = provider.get_events()
    print(f"✓ Loaded {len(events)} events")

    processed_events = events
    for hydrator in orchestrator.hydrators:
        processed_events = hydrator.hydrate(processed_events)
    print(f"✓ Processed events through pipeline")
    print()

    # Convert to timeline days
    print("Converting to timeline format...")
    processor = TimelineProcessor()
    timeline_days = processor.process(processed_events)
    print(f"✓ Generated {len(timeline_days)} timeline days")
    print()

    # Find the middle day (2026-01-02)
    target_date = "2026-01-02"
    target_day = None
    for day in timeline_days:
        if day.date_str == target_date:
            target_day = day
            break

    if not target_day:
        print(f"ERROR: Target day {target_date} not found in timeline")
        return 1

    print(f"✓ Found target day: {target_date}")
    print(f"  Day header: {target_day.day_header}")
    print(f"  Events: {len(target_day.events)}")
    print()

    # Setup AI cache and banner generator
    cache_dir = Path("output/test_banner/.ai_cache")
    cache_dir.mkdir(parents=True, exist_ok=True)

    print("Initializing banner generator...")
    client = GeminiClient(api_key=api_key)
    ai_cache = AiCache(cache_dir)
    banner_hydrator = BannerImageHydrator(
        client=client,
        cache=ai_cache,
        model="gemini-3-pro-image-preview",
        force_refresh=True  # Force generation for testing
    )
    print("✓ Banner generator initialized")
    print()

    # Generate banner (API CALL HAPPENS HERE)
    print("=" * 70)
    print("GENERATING BANNER IMAGE (API CALL)")
    print("=" * 70)
    print()

    enriched_days = banner_hydrator.hydrate([target_day])
    enriched_day = enriched_days[0]

    # Validate result
    if not enriched_day.banner_image_path:
        print("ERROR: No banner image path returned")
        return 1

    banner_path = Path(enriched_day.banner_image_path)
    if not banner_path.exists():
        print(f"ERROR: Banner image not found at {banner_path}")
        return 1

    print(f"✓ Banner generated: {banner_path}")
    print()

    # Validate aspect ratio
    print("Validating image...")
    img = Image.open(banner_path)
    width, height = img.size
    aspect_ratio = width / height
    expected_ratio = 16 / 9

    print(f"  Dimensions: {width}x{height}")
    print(f"  Aspect ratio: {aspect_ratio:.4f}")
    print(f"  Expected: {expected_ratio:.4f}")
    print(f"  Difference: {abs(aspect_ratio - expected_ratio):.4f}")
    print()

    # Check if within tolerance (0.02 allows for API rounding/upscaling)
    # Gemini API may use internal resolution presets, so allow ~2% deviation
    is_correct = abs(aspect_ratio - expected_ratio) < 0.02

    if is_correct:
        print("=" * 70)
        print("✓ SUCCESS: Banner image has correct 16:9 aspect ratio!")
        print("=" * 70)
        print()
        print(f"Banner saved to: {banner_path}")
        print("Please visually inspect the image to confirm style and quality.")
        return 0
    else:
        print("=" * 70)
        print("✗ FAILURE: Banner image aspect ratio is incorrect!")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    sys.exit(main())

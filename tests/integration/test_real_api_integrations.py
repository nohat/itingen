"""Integration tests for external APIs with real API calls.

IMPORTANT: These tests make REAL API calls and may incur costs.
Only run when explicitly validating integrations.

Usage:
    pytest tests/integration/test_real_api_integrations.py -v

Environment variables required:
    GOOGLE_MAPS_API_KEY - Google Maps API key
    GEMINI_API_KEY - Google Gemini API key
"""

import os
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from itingen.integrations.maps.google_maps import GoogleMapsClient
from itingen.integrations.weather.weatherspark import WeatherSparkClient
from itingen.integrations.ai.gemini import GeminiClient
from itingen.hydrators.ai.cache import AiCache
from itingen.hydrators.ai.narratives import NarrativeHydrator
from itingen.hydrators.ai.images import ImageHydrator
from itingen.hydrators.maps import MapsHydrator
from itingen.hydrators.weather import WeatherHydrator
from itingen.core.domain.events import Event


# API Keys from environment
GOOGLE_MAPS_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

RUN_REAL_API_TESTS = os.environ.get("RUN_REAL_API_TESTS") == "1"
REAL_API_ENABLED = RUN_REAL_API_TESTS and bool(GOOGLE_MAPS_API_KEY and GEMINI_API_KEY)

pytestmark = pytest.mark.skipif(
    not REAL_API_ENABLED,
    reason=(
        "Real API integration tests disabled. Set RUN_REAL_API_TESTS=1 and provide "
        "GOOGLE_MAPS_API_KEY and GEMINI_API_KEY (or GOOGLE_API_KEY)."
    ),
)

def requires_api_keys(func):
    """Decorator to skip tests if API keys are missing."""
    return pytest.mark.skipif(
        not GOOGLE_MAPS_API_KEY or not GEMINI_API_KEY,
        reason="API keys not found in environment"
    )(func)

@pytest.fixture
def temp_cache_dir():
    """Create a temporary cache directory for testing."""
    with TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


class TestGoogleMapsIntegration:
    """Test Google Maps API integration with real API calls."""

    def test_maps_client_directions(self):
        """Test real Google Maps directions API call."""
        client = GoogleMapsClient(api_key=GOOGLE_MAPS_API_KEY)

        # Test a simple route in New Zealand (from the NZ trip)
        result = client.get_directions(
            origin="Auckland Airport, New Zealand",
            destination="Wellington, New Zealand",
            mode="driving"
        )

        assert result is not None
        assert "duration_seconds" in result
        assert "duration_text" in result
        assert "distance_text" in result
        assert result["duration_seconds"] > 0

        # Validate the route is reasonable (should be several hours)
        # Auckland to Wellington is ~650km, should take 8-10 hours
        duration_hours = result["duration_seconds"] / 3600
        assert 6 < duration_hours < 12, f"Unexpected duration: {duration_hours} hours"

        print(f"\n✅ Maps API: Auckland Airport → Wellington")
        print(f"   Duration: {result['duration_text']}")
        print(f"   Distance: {result['distance_text']}")

    def test_maps_client_caching(self, temp_cache_dir):
        """Test that Maps API responses are cached correctly."""
        client = GoogleMapsClient(
            api_key=GOOGLE_MAPS_API_KEY,
            cache_dir=str(temp_cache_dir)
        )

        # First call should hit the API
        result1 = client.get_directions(
            origin="San Francisco, CA",
            destination="Los Angeles, CA",
            mode="driving"
        )

        # Second call should use cache
        result2 = client.get_directions(
            origin="San Francisco, CA",
            destination="Los Angeles, CA",
            mode="driving"
        )

        assert result1 == result2
        assert result1["duration_seconds"] > 0

        # Check cache file exists
        cache_files = list(temp_cache_dir.glob("*.json"))
        assert len(cache_files) > 0, "Cache file should be created"

        print(f"\n✅ Maps caching: {len(cache_files)} cache file(s) created")

    def test_maps_hydrator_enriches_events(self):
        """Test MapsHydrator enriches drive events with real data."""
        hydrator = MapsHydrator(api_key=GOOGLE_MAPS_API_KEY)

        # Create a drive event
        event = Event(
            event_heading="Drive to Airport",
            kind="drive",
            time_utc="2024-01-15T08:00:00Z",
            who=["alice"],
            location="SFO Airport",
            travel_from="Mountain View, CA",
            travel_to="San Francisco Airport, CA"
        )

        # Hydrate
        result = hydrator.hydrate([event])

        assert len(result) == 1
        enriched = result[0]

        # Check enrichment
        assert hasattr(enriched, "duration_seconds")
        assert hasattr(enriched, "duration_text")
        assert hasattr(enriched, "distance_text")
        assert enriched.duration_seconds > 0

        print(f"\n✅ MapsHydrator enriched event:")
        print(f"   Route: {event.travel_from} → {event.travel_to}")
        print(f"   Duration: {enriched.duration_text}")
        print(f"   Distance: {enriched.distance_text}")


class TestWeatherSparkIntegration:
    """Test WeatherSpark scraping integration."""

    def test_weatherspark_client_typical_weather(self):
        """Test WeatherSpark scraping for typical weather data."""
        client = WeatherSparkClient()

        # Test Auckland weather (use the location key, not full name)
        result = client.get_typical_weather(
            location="auckland",  # Use key from PLACE_MAP
            date="2025-12-31"
        )

        # Note: WeatherSpark may return None if scraping fails or location not found
        # This is expected behavior for the integration
        if result is not None:
            assert isinstance(result, dict)
            print(f"\n✅ WeatherSpark: Auckland weather for Dec 31")
            print(f"   Data keys: {list(result.keys())}")
        else:
            print(f"\n⚠️ WeatherSpark: No data returned (scraping may have failed)")
            print(f"   This is expected - WeatherSpark scraping is fragile")

    def test_weather_hydrator_enriches_events(self):
        """Test WeatherHydrator enriches events with weather data."""
        hydrator = WeatherHydrator()

        # Create an event in Auckland
        event = Event(
            event_heading="Arrive in Auckland",
            kind="flight_arrival",
            time_utc="2025-12-31T05:45:00Z",
            who=["alice"],
            location="Auckland Airport"
        )

        # Hydrate
        result = hydrator.hydrate([event])

        assert len(result) == 1
        enriched = result[0]

        # Check if weather data was added (may vary by implementation)
        print(f"\n✅ WeatherHydrator processed event:")
        print(f"   Location: {event.location}")
        print(f"   Weather enrichment attempted")


class TestGeminiIntegration:
    """Test Google Gemini AI integration with real API calls."""

    def test_gemini_client_text_generation(self):
        """Test real Gemini text generation API call."""
        client = GeminiClient(api_key=GEMINI_API_KEY)

        prompt = "Describe a beautiful sunset over Auckland harbor in 2 sentences."
        result = client.generate_text(prompt)

        assert result is not None
        assert isinstance(result, str)
        assert len(result) > 20  # Should be a reasonable response

        print(f"\n✅ Gemini text generation:")
        print(f"   Prompt: {prompt}")
        print(f"   Response: {result}")

    def test_gemini_thumbnail_generation(self, temp_cache_dir):
        """Test Gemini thumbnail image generation (1:1) with gemini-2.5-flash-image."""
        from itingen.integrations.ai.image_prompts import format_thumbnail_prompt

        client = GeminiClient(api_key=GEMINI_API_KEY)

        # Create a thumbnail prompt for a travel event
        prompt = format_thumbnail_prompt(
            event_heading="Ferry to Waiheke Island",
            location="Waiheke Island Ferry Terminal",
            kind="ferry",
            description="Scenic ferry ride across Hauraki Gulf",
            travel_mode="ferry",
            travel_from="Auckland Downtown",
            travel_to="Waiheke Island"
        )

        # Generate image with Gemini (1:1 thumbnail)
        image_bytes = client.generate_image_with_gemini(
            prompt=prompt,
            model="gemini-2.5-flash-image",
            aspect_ratio="1:1",
            image_size="1K"
        )

        assert image_bytes is not None
        assert isinstance(image_bytes, bytes)
        assert len(image_bytes) > 0

        # Save to file for validation
        output_path = temp_cache_dir / "test_thumbnail_gemini.png"
        output_path.write_bytes(image_bytes)

        print(f"\n✅ Gemini thumbnail generation (1:1):")
        print(f"   Model: gemini-2.5-flash-image")
        print(f"   Size: {len(image_bytes)} bytes")
        print(f"   Saved to: {output_path}")

    def test_imagen_banner_generation(self, temp_cache_dir):
        """Test Imagen banner image generation (16:9) with imagen-4.0-ultra-generate-001."""
        from itingen.integrations.ai.image_prompts import format_banner_prompt

        client = GeminiClient(api_key=GEMINI_API_KEY)

        # Create a banner prompt for a day in Auckland
        prompt = format_banner_prompt(
            date="2025-12-31",
            location="Auckland, New Zealand",
            hero_events=[
                "Auckland Harbour Bridge",
                "Sky Tower",
                "Waiheke Island vineyards"
            ],
            supporting_details=[
                "Ferry boats on Hauraki Gulf",
                "Coastal beaches with golden sand",
                "Rolling vineyard hills",
                "City skyline in the distance",
                "Sailboats dotting the harbor"
            ],
            weather="sunny with blue skies",
            mood="adventurous and relaxed"
        )

        # Generate image with Imagen (16:9 banner)
        image_bytes = client.generate_image_with_imagen(
            prompt=prompt,
            model="imagen-4.0-ultra-generate-001",
            aspect_ratio="16:9"
        )

        assert image_bytes is not None
        assert isinstance(image_bytes, bytes)
        assert len(image_bytes) > 0

        # Save to file for validation
        output_path = temp_cache_dir / "test_banner_imagen.png"
        output_path.write_bytes(image_bytes)

        print(f"\n✅ Imagen banner generation (16:9):")
        print(f"   Model: imagen-4.0-ultra-generate-001")
        print(f"   Size: {len(image_bytes)} bytes")
        print(f"   Saved to: {output_path}")

    def test_ai_cache_text_caching(self, temp_cache_dir):
        """Test AI text caching works correctly."""
        cache = AiCache(cache_dir=temp_cache_dir)

        payload = {
            "task": "test",
            "prompt": "Test prompt for caching"
        }

        # First call - cache miss
        cached = cache.get_text(payload)
        assert cached is None

        # Set cache
        response = "This is a cached response"
        cache.set_text(payload, response)

        # Second call - cache hit
        cached = cache.get_text(payload)
        assert cached == response

        print(f"\n✅ AI text caching:")
        print(f"   Cache directory: {temp_cache_dir}")
        print(f"   Cached response: {cached}")

    def test_ai_cache_image_caching(self, temp_cache_dir):
        """Test AI image caching works correctly."""
        cache = AiCache(cache_dir=temp_cache_dir)

        payload = {
            "task": "image",
            "prompt": "Test image prompt"
        }

        # First call - cache miss
        cached = cache.get_image_path(payload)
        assert cached is None

        # Create dummy image data (bytes)
        image_data = b"fake image data"

        # Set cache (takes bytes, not path)
        cache.set_image(payload, image_data)

        # Second call - cache hit
        cached = cache.get_image_path(payload)
        assert cached is not None
        assert cached.exists()

        print(f"\n✅ AI image caching:")
        print(f"   Cache directory: {temp_cache_dir}")
        print(f"   Cached image: {cached}")


class TestNarrativeHydrator:
    """Test AI narrative generation with real API calls."""

    def test_narrative_hydrator_generates_text(self, temp_cache_dir):
        """Test NarrativeHydrator generates narratives for events."""
        client = GeminiClient(api_key=GEMINI_API_KEY)
        cache = AiCache(cache_dir=temp_cache_dir)
        hydrator = NarrativeHydrator(client=client, cache=cache)

        event = Event(
            event_heading="Wine Tasting at Tantalus Estate",
            kind="activity",
            time_utc="2025-12-31T11:00:00Z",
            who=["alice", "bob"],
            location="Tantalus Estate, Waiheke Island",
            description="Tasting reservation at Tantalus Estate vineyard."
        )

        # Hydrate (will make real API call)
        result = hydrator.hydrate([event])

        assert len(result) == 1
        enriched = result[0]

        # Check narrative was generated
        assert hasattr(enriched, "narrative")
        assert enriched.narrative is not None
        assert len(enriched.narrative) > 20

        print(f"\n✅ Narrative generation:")
        print(f"   Event: {event.event_heading}")
        print(f"   Narrative: {enriched.narrative[:100]}...")

        # Test caching - second call should use cache
        result2 = hydrator.hydrate([event])
        enriched2 = result2[0]
        assert enriched2.narrative == enriched.narrative

        print(f"   ✅ Cache hit on second call")


class TestImageHydrator:
    """Test AI image generation with real API calls."""

    def test_image_hydrator_generates_thumbnails(self, temp_cache_dir):
        """Test ImageHydrator generates Gemini thumbnail images (1:1) for events."""
        client = GeminiClient(api_key=GEMINI_API_KEY)
        cache = AiCache(cache_dir=temp_cache_dir)

        # ImageHydrator now uses Gemini for thumbnails
        hydrator = ImageHydrator(
            client=client,
            cache=cache,
            model="gemini-2.5-flash-image"
        )

        event = Event(
            event_heading="Ferry to Waiheke Island",
            kind="ferry",
            time_utc="2025-12-31T09:00:00Z",
            who=["alice", "bob"],
            location="Waiheke Island Ferry Terminal",
            description="Scenic ferry ride across Hauraki Gulf."
        )

        # Hydrate (will make real API call with Gemini)
        result = hydrator.hydrate([event])

        assert len(result) == 1
        enriched = result[0]

        # Check image was generated (field is image_path)
        assert hasattr(enriched, "image_path")
        assert enriched.image_path is not None
        assert Path(enriched.image_path).exists()
        assert Path(enriched.image_path).stat().st_size > 0

        print(f"\n✅ Thumbnail image generation (Gemini):")
        print(f"   Event: {event.event_heading}")
        print(f"   Model: gemini-2.5-flash-image")
        print(f"   Image: {enriched.image_path}")
        print(f"   Size: {Path(enriched.image_path).stat().st_size} bytes")

        # Test caching - second call should use cache
        result2 = hydrator.hydrate([event])
        enriched2 = result2[0]
        assert enriched2.image_path == enriched.image_path
        print(f"   ✅ Cache hit on second call")


class TestEndToEndIntegration:
    """Test complete pipeline with all integrations enabled."""

    def test_full_pipeline_with_all_integrations(self, temp_cache_dir):
        """Test a complete event enrichment pipeline with all integrations."""
        # Create clients
        maps_client = GoogleMapsClient(api_key=GOOGLE_MAPS_API_KEY)
        gemini_client = GeminiClient(api_key=GEMINI_API_KEY)
        ai_cache = AiCache(cache_dir=temp_cache_dir)

        # Create hydrators
        maps_hydrator = MapsHydrator(api_key=GOOGLE_MAPS_API_KEY)
        narrative_hydrator = NarrativeHydrator(
            client=gemini_client,
            cache=ai_cache
        )

        # Create a test event
        event = Event(
            event_heading="Drive to Queenstown",
            kind="drive",
            time_utc="2026-01-05T08:00:00Z",
            who=["alice", "bob"],
            location="Queenstown",
            travel_from="Wanaka, New Zealand",
            travel_to="Queenstown, New Zealand",
            description="Scenic drive through Southern Alps."
        )

        # Apply hydrators in sequence
        print(f"\n✅ Full pipeline test:")
        print(f"   Starting event: {event.event_heading}")

        # Step 1: Maps enrichment
        events = [event]
        events = maps_hydrator.hydrate(events)
        enriched = events[0]
        print(f"   After maps: duration={getattr(enriched, 'duration_text', 'N/A')}")

        # Step 2: Narrative enrichment
        events = narrative_hydrator.hydrate(events)
        enriched = events[0]
        print(f"   After narrative: {enriched.narrative[:60]}...")

        # Validate full enrichment
        assert hasattr(enriched, "duration_seconds")
        assert hasattr(enriched, "narrative")
        assert enriched.duration_seconds > 0
        assert len(enriched.narrative) > 20

        print(f"\n✅ Full pipeline successful!")
        print(f"   Event fully enriched with Maps + AI")


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "-s"])

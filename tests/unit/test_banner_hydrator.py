"""Tests for BannerImageHydrator."""

import os
import tempfile
from unittest.mock import Mock, patch
from pathlib import Path
import io

import pytest
from PIL import Image

from itingen.hydrators.ai.banner import BannerImageHydrator, BannerCachePolicy
from itingen.hydrators.ai.cache import AiCache
from itingen.integrations.ai.gemini import GeminiClient
from itingen.rendering.timeline import TimelineDay
from itingen.core.domain.events import Event


@pytest.fixture
def mock_gemini_client():
    """Create a mock GeminiClient."""
    # Create valid image bytes for post-processing
    img = Image.new('RGB', (1600, 900), color='blue')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    client = Mock(spec=GeminiClient)
    client.generate_image_with_gemini.return_value = img_bytes.getvalue()
    return client


@pytest.fixture
def temp_cache_dir():
    """Create a temporary cache directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def mock_cache(temp_cache_dir):
    """Create a mock AiCache."""
    cache = Mock(spec=AiCache)
    cache.cache_dir = temp_cache_dir
    cache.image_cache = temp_cache_dir / "images"
    cache.image_cache.mkdir(exist_ok=True)
    cache.get_image_path.return_value = None
    cache.set_image.return_value = None
    return cache


@pytest.fixture
def sample_events():
    """Create sample events for testing."""
    return [
        Event(
            date="2025-12-31",
            event_heading="Morning Hike",
            location="Queenstown",
            kind="activity",
            description="Hike up Ben Lomond"
        ),
        Event(
            date="2025-12-31",
            event_heading="Lunch at Fergburger",
            location="Queenstown", 
            kind="meal",
            description="Famous burger joint"
        ),
        Event(
            date="2025-12-31",
            event_heading="Scenic Gondola",
            location="Queenstown",
            kind="activity", 
            description="Ride the gondola for views"
        )
    ]


@pytest.fixture
def sample_timeline_day(sample_events):
    """Create a sample TimelineDay for testing."""
    return TimelineDay(
        date_str="2025-12-31",
        day_header="December 31, 2025",
        events=sample_events
    )


class TestBannerImageHydrator:
    """Test suite for BannerImageHydrator."""

    def test_initialization(self, mock_gemini_client):
        """Test BannerImageHydrator initialization."""
        hydrator = BannerImageHydrator(mock_gemini_client)
        
        assert hydrator.client == mock_gemini_client
        assert hydrator.cache is None
        assert hydrator.cache_policy == BannerCachePolicy.STABLE_DATE
        assert hydrator.model == "gemini-3-pro-image-preview"
        assert hydrator.force_refresh is False

    def test_initialization_with_cache(self, mock_gemini_client, mock_cache):
        """Test initialization with cache and custom settings."""
        hydrator = BannerImageHydrator(
            mock_gemini_client,
            cache=mock_cache,
            cache_policy=BannerCachePolicy.FINGERPRINT,
            model="gemini-2.5-flash-image",
            force_refresh=True
        )
        
        assert hydrator.cache == mock_cache
        assert hydrator.cache_policy == BannerCachePolicy.FINGERPRINT
        assert hydrator.model == "gemini-2.5-flash-image"
        assert hydrator.force_refresh is True

    def test_initialization_with_env_var(self, mock_gemini_client):
        """Test initialization respects environment variable."""
        with patch.dict(os.environ, {"BANNER_MODEL": "custom-model"}):
            hydrator = BannerImageHydrator(mock_gemini_client)
            assert hydrator.model == "custom-model"

    def test_cache_key_stable_date(self, mock_gemini_client, sample_timeline_day):
        """Test cache key generation with STABLE_DATE policy."""
        hydrator = BannerImageHydrator(
            mock_gemini_client,
            cache_policy=BannerCachePolicy.STABLE_DATE
        )
        
        key = hydrator._cache_key(sample_timeline_day)
        assert key == "banner_2025-12-31"

    def test_cache_key_fingerprint(self, mock_gemini_client, sample_timeline_day):
        """Test cache key generation with FINGERPRINT policy."""
        hydrator = BannerImageHydrator(
            mock_gemini_client,
            cache_policy=BannerCachePolicy.FINGERPRINT
        )
        
        key = hydrator._cache_key(sample_timeline_day)
        assert key.startswith("banner_2025-12-31_")
        assert len(key) > 20  # Should have fingerprint suffix

    def test_cache_key_hybrid(self, mock_gemini_client, sample_timeline_day):
        """Test cache key generation with HYBRID policy."""
        hydrator = BannerImageHydrator(
            mock_gemini_client,
            cache_policy=BannerCachePolicy.HYBRID
        )
        
        key = hydrator._cache_key(sample_timeline_day)
        assert key.startswith("banner_2025-12-31_")
        # Hybrid should have 8-char fingerprint suffix
        suffix = key.split("_")[-1]
        assert len(suffix) == 8

    def test_primary_location_extraction(self, mock_gemini_client, sample_timeline_day):
        """Test primary location extraction from events."""
        hydrator = BannerImageHydrator(mock_gemini_client)
        
        location = hydrator._primary_location(sample_timeline_day)
        assert location == "Queenstown"

    def test_primary_location_fallback(self, mock_gemini_client, sample_events):
        """Test primary location fallback when no locations."""
        # Remove locations from events
        for event in sample_events:
            event.location = None
            
        day = TimelineDay(
            date_str="2025-12-31",
            day_header="December 31, 2025",
            events=sample_events
        )
        
        hydrator = BannerImageHydrator(mock_gemini_client)
        location = hydrator._primary_location(day)
        assert location == "the destination"

    def test_hero_events_extraction(self, mock_gemini_client, sample_timeline_day):
        """Test hero events extraction."""
        hydrator = BannerImageHydrator(mock_gemini_client)
        
        hero_events = hydrator._hero_events(sample_timeline_day)
        assert len(hero_events) == 3
        assert "Morning Hike" in hero_events
        assert "Lunch at Fergburger" in hero_events
        assert "Scenic Gondola" in hero_events

    def test_hero_events_limit(self, mock_gemini_client):
        """Test hero events extraction respects limit."""
        # Create day with more than 3 events
        events = [
            Event(date="2025-12-31", event_heading=f"Event {i}", location="Test")
            for i in range(10)
        ]
        day = TimelineDay(
            date_str="2025-12-31",
            day_header="December 31, 2025", 
            events=events
        )
        
        hydrator = BannerImageHydrator(mock_gemini_client)
        hero_events = hydrator._hero_events(day)
        assert len(hero_events) == 3  # Should be limited to 3

    def test_banner_prompt_generation(self, mock_gemini_client, sample_timeline_day):
        """Test banner prompt generation."""
        hydrator = BannerImageHydrator(mock_gemini_client)
        
        prompt = hydrator._banner_prompt(sample_timeline_day)
        
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        # Check that key elements are in the prompt (may be formatted differently)
        assert "Queenstown" in prompt
        assert "Morning Hike" in prompt
        # Check for style elements
        assert "vibrant isometric vector illustration" in prompt or "Ligne Claire" in prompt

    def test_hydrate_without_cache(self, mock_gemini_client, sample_timeline_day):
        """Test hydration without cache generates new image."""
        hydrator = BannerImageHydrator(mock_gemini_client)
        
        result_days = hydrator.hydrate([sample_timeline_day])
        
        assert len(result_days) == 1
        result_day = result_days[0]
        # Should have banner_image_path set (even if it's a computed path)
        assert hasattr(result_day, 'banner_image_path')
        
        # Verify Gemini client was called
        mock_gemini_client.generate_image_with_gemini.assert_called_once()

    def test_hydrate_with_cache_miss(self, mock_gemini_client, mock_cache, sample_timeline_day):
        """Test hydration with cache miss generates new image."""
        # Configure cache to return None on first call (miss), then path on second call (after set)
        cached_path = Path("/cached/banner.png")
        mock_cache.get_image_path.side_effect = [None, cached_path]

        hydrator = BannerImageHydrator(mock_gemini_client, cache=mock_cache)

        result_days = hydrator.hydrate([sample_timeline_day])

        assert len(result_days) == 1
        assert hasattr(result_days[0], 'banner_image_path')

        # Verify cache was checked twice (before and after set) and image was generated
        assert mock_cache.get_image_path.call_count == 2
        mock_cache.set_image.assert_called_once()
        mock_gemini_client.generate_image_with_gemini.assert_called_once()

    def test_hydrate_with_cache_hit(self, mock_gemini_client, mock_cache, sample_timeline_day):
        """Test hydration with cache hit uses cached image."""
        # Configure cache to return a path (hit)
        cached_path = Path("/cached/banner.png")
        mock_cache.get_image_path.return_value = cached_path
        
        hydrator = BannerImageHydrator(mock_gemini_client, cache=mock_cache)
        
        result_days = hydrator.hydrate([sample_timeline_day])
        
        assert len(result_days) == 1
        assert result_days[0].banner_image_path == str(cached_path)
        
        # Verify cache was checked but no new image was generated
        mock_cache.get_image_path.assert_called_once()
        mock_cache.set_image.assert_not_called()
        mock_gemini_client.generate_image_with_gemini.assert_not_called()

    def test_hydrate_with_force_refresh(self, mock_gemini_client, mock_cache, sample_timeline_day):
        """Test hydration with force_refresh ignores cache on check but uses it for path retrieval."""
        # Configure cache to return a path when called after set
        cached_path = Path("/cached/banner.png")
        mock_cache.get_image_path.return_value = cached_path

        hydrator = BannerImageHydrator(
            mock_gemini_client,
            cache=mock_cache,
            force_refresh=True
        )

        result_days = hydrator.hydrate([sample_timeline_day])

        assert len(result_days) == 1
        assert hasattr(result_days[0], 'banner_image_path')

        # Verify cache check was skipped during force refresh, but called once after set to get path
        mock_cache.get_image_path.assert_called_once()
        mock_cache.set_image.assert_called_once()
        mock_gemini_client.generate_image_with_gemini.assert_called_once()

    def test_hydrate_multiple_days(self, mock_gemini_client, sample_events):
        """Test hydration with multiple timeline days."""
        # Create two days
        day1 = TimelineDay(
            date_str="2025-12-31",
            day_header="December 31, 2025",
            events=sample_events
        )
        day2 = TimelineDay(
            date_str="2026-01-01", 
            day_header="January 1, 2026",
            events=sample_events
        )
        
        hydrator = BannerImageHydrator(mock_gemini_client)
        
        result_days = hydrator.hydrate([day1, day2])
        
        assert len(result_days) == 2
        assert all(hasattr(day, 'banner_image_path') for day in result_days)
        
        # Should generate images for both days
        assert mock_gemini_client.generate_image_with_gemini.call_count == 2

    def test_banner_payload_structure(self, mock_gemini_client, sample_timeline_day):
        """Test banner payload structure for fingerprinting."""
        hydrator = BannerImageHydrator(mock_gemini_client)
        
        payload = hydrator._banner_payload(sample_timeline_day)
        
        assert payload["task"] == "day_banner"
        assert payload["model"] == "gemini-3-pro-image-preview"
        assert payload["date"] == "2025-12-31"
        assert "hero_events" in payload
        assert "location" in payload
        assert isinstance(payload["hero_events"], list)

    def test_empty_events_handling(self, mock_gemini_client):
        """Test handling of timeline day with no events."""
        empty_day = TimelineDay(
            date_str="2025-12-31",
            day_header="December 31, 2025",
            events=[]
        )
        
        hydrator = BannerImageHydrator(mock_gemini_client)
        
        # Should not raise errors
        location = hydrator._primary_location(empty_day)
        assert location == "the destination"
        
        hero_events = hydrator._hero_events(empty_day)
        assert hero_events == []
        
        prompt = hydrator._banner_prompt(empty_day)
        assert isinstance(prompt, str)
        assert len(prompt) > 0

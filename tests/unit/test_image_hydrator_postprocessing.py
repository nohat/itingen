import pytest
from unittest.mock import Mock, MagicMock
from PIL import Image
import io
from itingen.hydrators.ai.images import ImageHydrator
from itingen.hydrators.ai.banner import BannerImageHydrator
from itingen.core.domain.events import Event
from itingen.rendering.timeline import TimelineDay


class TestImageHydratorPostProcessing:
    """Test that ImageHydrator applies post-processing before caching."""
    
    def test_thumbnail_applies_postprocessing_before_cache(self):
        """Should post-process thumbnail images before caching."""
        mock_client = Mock()
        mock_cache = Mock()
        
        img_with_border = Image.new('RGB', (220, 220), color='white')
        inner = Image.new('RGB', (100, 100), color='blue')
        img_with_border.paste(inner, (60, 60))
        
        img_bytes = io.BytesIO()
        img_with_border.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        raw_bytes = img_bytes.getvalue()
        
        mock_client.generate_image_with_gemini.return_value = raw_bytes
        mock_cache.get_image_path.return_value = None
        
        hydrator = ImageHydrator(client=mock_client, cache=mock_cache)
        event = Event(
            event_heading="Test Event",
            location="Test Location",
            kind="activity"
        )
        
        result = hydrator.hydrate([event])
        
        assert mock_cache.set_image.called
        cached_bytes = mock_cache.set_image.call_args[0][1]
        
        cached_img = Image.open(io.BytesIO(cached_bytes))
        assert cached_img.size[0] < 220
        assert cached_img.size[1] < 220
    
    def test_thumbnail_maintains_1_1_aspect_ratio(self):
        """Should ensure 1:1 aspect ratio for thumbnails."""
        mock_client = Mock()
        mock_cache = Mock()
        
        img_rect = Image.new('RGB', (200, 100), color='red')
        img_bytes = io.BytesIO()
        img_rect.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        mock_client.generate_image_with_gemini.return_value = img_bytes.getvalue()
        mock_cache.get_image_path.return_value = None
        
        hydrator = ImageHydrator(client=mock_client, cache=mock_cache)
        event = Event(
            event_heading="Test Event",
            location="Test Location"
        )
        
        result = hydrator.hydrate([event])
        
        cached_bytes = mock_cache.set_image.call_args[0][1]
        cached_img = Image.open(io.BytesIO(cached_bytes))
        
        assert cached_img.size[0] == cached_img.size[1]


class TestBannerHydratorPostProcessing:
    """Test that BannerImageHydrator applies post-processing before caching."""
    
    def test_banner_applies_postprocessing_before_cache(self):
        """Should post-process banner images before caching."""
        from pathlib import Path
        
        mock_client = Mock()
        mock_cache = Mock()
        
        img_with_border = Image.new('RGB', (1920, 1080), color=(245, 245, 245))
        inner = Image.new('RGB', (1600, 900), color='green')
        img_with_border.paste(inner, (160, 90))
        
        img_bytes = io.BytesIO()
        img_with_border.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        raw_bytes = img_bytes.getvalue()
        
        mock_client.generate_image_with_gemini.return_value = raw_bytes
        mock_cache.get_image_path.return_value = None
        
        mock_prompt_file = Mock()
        mock_prompt_file.write_text = Mock()
        mock_cache.cache_dir = Mock()
        mock_cache.cache_dir.__truediv__ = Mock(return_value=mock_prompt_file)
        mock_cache.image_cache = Path("/tmp/test_cache")
        
        hydrator = BannerImageHydrator(client=mock_client, cache=mock_cache)
        
        day = TimelineDay(
            date_str="2026-01-15",
            day_header="Day 1",
            events=[]
        )
        
        result = hydrator.hydrate([day])
        
        assert mock_cache.set_image.called
        cached_bytes = mock_cache.set_image.call_args[0][1]
        
        cached_img = Image.open(io.BytesIO(cached_bytes))
        assert cached_img.size[0] < 1920
        assert cached_img.size[1] < 1080
    
    def test_banner_maintains_16_9_aspect_ratio(self):
        """Should ensure 16:9 aspect ratio for banners."""
        from pathlib import Path
        
        mock_client = Mock()
        mock_cache = Mock()
        
        img_square = Image.new('RGB', (1000, 1000), color='purple')
        img_bytes = io.BytesIO()
        img_square.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        mock_client.generate_image_with_gemini.return_value = img_bytes.getvalue()
        mock_cache.get_image_path.return_value = None
        
        mock_prompt_file = Mock()
        mock_prompt_file.write_text = Mock()
        mock_cache.cache_dir = Mock()
        mock_cache.cache_dir.__truediv__ = Mock(return_value=mock_prompt_file)
        mock_cache.image_cache = Path("/tmp/test_cache")
        
        hydrator = BannerImageHydrator(client=mock_client, cache=mock_cache)
        
        day = TimelineDay(
            date_str="2026-01-15",
            day_header="Day 1",
            events=[]
        )
        
        result = hydrator.hydrate([day])
        
        cached_bytes = mock_cache.set_image.call_args[0][1]
        cached_img = Image.open(io.BytesIO(cached_bytes))
        
        ratio = cached_img.size[0] / cached_img.size[1]
        expected_ratio = 16 / 9
        assert abs(ratio - expected_ratio) < 0.01

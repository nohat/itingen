import pytest
from unittest.mock import patch
from PIL import Image
import io
from itingen.core.domain.events import Event
from itingen.hydrators.ai.narratives import NarrativeHydrator
from itingen.hydrators.ai.images import ImageHydrator
from itingen.hydrators.ai.cache import AiCache

@pytest.fixture
def mock_gemini_client():
    with patch("itingen.integrations.ai.gemini.GeminiClient") as mock:
        yield mock.return_value

@pytest.fixture
def mock_cache(tmp_path):
    return AiCache(tmp_path)

@pytest.fixture
def sample_events():
    return [
        Event(
            event_heading="Visit Tokyo Tower",
            kind="activity",
            location="Tokyo Tower",
            description="Sightseeing"
        )
    ]

def test_narrative_hydrator_enriches_events(mock_gemini_client, mock_cache, sample_events):
    mock_gemini_client.generate_text.return_value = "A beautiful visit to Tokyo Tower."
    
    hydrator = NarrativeHydrator(client=mock_gemini_client, cache=mock_cache)
    hydrated_events = hydrator.hydrate(sample_events)
    
    assert hydrated_events[0].narrative == "A beautiful visit to Tokyo Tower."
    mock_gemini_client.generate_text.assert_called_once()
    
    # Test caching
    mock_gemini_client.generate_text.reset_mock()
    hydrated_events_cached = hydrator.hydrate(sample_events)
    assert hydrated_events_cached[0].narrative == "A beautiful visit to Tokyo Tower."
    mock_gemini_client.generate_text.assert_not_called()

def test_image_hydrator_enriches_events(mock_gemini_client, mock_cache, sample_events):
    # Create valid image bytes for post-processing
    img = Image.new('RGB', (100, 100), color='blue')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    mock_gemini_client.generate_image_with_gemini.return_value = img_bytes.getvalue()
    
    hydrator = ImageHydrator(client=mock_gemini_client, cache=mock_cache)
    hydrated_events = hydrator.hydrate(sample_events)
    
    assert hydrated_events[0].image_path is not None
    assert str(hydrated_events[0].image_path).endswith(".png")  # AiCache uses .png extension for post-processed images
    mock_gemini_client.generate_image_with_gemini.assert_called_once()
    
    # Test caching
    mock_gemini_client.generate_image_with_gemini.reset_mock()
    hydrated_events_cached = hydrator.hydrate(sample_events)
    assert hydrated_events_cached[0].image_path == hydrated_events[0].image_path
    mock_gemini_client.generate_image_with_gemini.assert_not_called()

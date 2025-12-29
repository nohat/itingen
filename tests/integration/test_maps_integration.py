import pytest
from pathlib import Path
from unittest.mock import patch
from itingen.core.domain.events import Event
from itingen.pipeline.orchestrator import PipelineOrchestrator
from itingen.hydrators.maps import MapsHydrator
from itingen.rendering.markdown import MarkdownEmitter
from itingen.providers.file_provider import LocalFileProvider

class MockMapsProvider(LocalFileProvider):
    def get_events(self):
        return [
            Event(
                event_heading="Drive to Auckland",
                kind="drive",
                travel_from="Hamilton",
                travel_to="Auckland"
            )
        ]
    def get_venues(self): return {}
    def get_config(self): return {}

def test_pipeline_with_maps_hydrator(tmp_path):
    # Mock the Google Maps Client to avoid actual API calls
    with patch("itingen.hydrators.maps.GoogleMapsClient") as MockClient:
        mock_client = MockClient.return_value
        mock_client.get_directions.return_value = {
            "duration_seconds": 5400,
            "duration_text": "1 hour 30 mins",
            "distance_text": "125 km"
        }

        provider = MockMapsProvider(tmp_path)
        # Create a dummy trip structure for LocalFileProvider initialization
        (tmp_path / "events").mkdir()
        (tmp_path / "venues").mkdir()
        
        hydrator = MapsHydrator(api_key="fake-key")
        emitter = MarkdownEmitter()
        
        orchestrator = PipelineOrchestrator(
            provider=provider,
            hydrators=[hydrator],
            emitters=[emitter]
        )
        
        output_dir = tmp_path / "output"
        events = orchestrator.execute(output_dir=output_dir)
        
        # Verify hydration
        assert events[0].duration_seconds == 5400
        assert events[0].duration_text == "1 hour 30 mins"
        
        # Verify output
        output_file = output_dir / "output_0.md"
        assert output_file.exists()
        content = output_file.read_text()
        assert "1 hour 30 mins" in content

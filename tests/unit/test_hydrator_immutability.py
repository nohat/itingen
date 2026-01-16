from itingen.core.domain.events import Event
from itingen.hydrators.maps import MapsHydrator
from itingen.pipeline.sorting import ChronologicalSorter
from itingen.pipeline.filtering import PersonFilter
from unittest.mock import patch

class TestHydratorImmutability:
    @patch('itingen.hydrators.maps.GoogleMapsClient')
    def test_maps_hydrator_immutability(self, mock_client_cls):
        # Setup
        # Configure the mock instance that will be returned when MapsHydrator instantiates GoogleMapsClient
        mock_client_instance = mock_client_cls.return_value
        mock_client_instance.get_directions.return_value = {
            "duration_seconds": 3600,
            "duration_text": "1 hour",
            "distance_text": "100 km"
        }

        event = Event(
            kind="drive",
            travel_from="A",
            travel_to="B",
            description="Drive from A to B"
        )
        
        # Act
        # We can pass any key, the mock client class will catch the init call
        hydrator = MapsHydrator(api_key="fake")
        results = hydrator.hydrate([event])
        
        # Assert
        assert len(results) == 1
        result = results[0]
        
        # Check that result is updated
        assert result.duration_seconds == 3600
        
        # CRITICAL: Check that original event is UNCHANGED
        assert getattr(event, "duration_seconds", None) is None, "Original event should not be mutated"
        assert event is not result, "Hydrator should return new objects"

    def test_chronological_sorter_immutability(self):
        # Sorting might reorder the list, but shouldn't mutate elements.
        # However, checking if it returns a new list is also good practice.
        e1 = Event(time_utc="2023-01-02T10:00:00Z")
        e2 = Event(time_utc="2023-01-01T10:00:00Z")
        events = [e1, e2]
        
        hydrator = ChronologicalSorter()
        results = hydrator.hydrate(events)
        
        assert results == [e2, e1]
        assert results is not events, "Should return a new list"
        # Sorter doesn't mutate items, so that's fine.

    def test_person_filter_immutability(self):
        e1 = Event(who=["alice"])
        e2 = Event(who=["bob"])
        events = [e1, e2]
        
        hydrator = PersonFilter(person_slug="alice")
        results = hydrator.hydrate(events)
        
        assert len(results) == 1
        assert results[0] == e1
        assert results is not events, "Should return a new list"

    @patch('itingen.hydrators.weather.WeatherSparkClient')
    def test_weather_hydrator_immutability(self, mock_client_cls):
        # Setup
        mock_client = mock_client_cls.return_value
        mock_client.get_typical_weather.return_value = {
            "high_temp_f": 75,
            "low_temp_f": 60,
            "conditions": "Sunny"
        }
        
        event = Event(
            location="Paris",
            time_utc="2023-06-01T10:00:00Z"
        )
        
        from itingen.hydrators.weather import WeatherHydrator
        hydrator = WeatherHydrator()
        
        # Act
        results = hydrator.hydrate([event])
        
        # Assert
        assert len(results) == 1
        result = results[0]
        
        # Check result updated
        assert getattr(result, "weather_temp_high") == 75
        
        # Check original unchanged
        assert getattr(event, "weather_temp_high", None) is None
        assert event is not result

    @patch('itingen.hydrators.ai.narratives.GeminiClient')
    def test_narrative_hydrator_immutability(self, mock_client_cls):
        mock_client = mock_client_cls.return_value
        mock_client.generate_text.return_value = "A cool story"
        
        event = Event(event_heading="Visit Paris", kind="activity")
        
        from itingen.hydrators.ai.narratives import NarrativeHydrator
        hydrator = NarrativeHydrator(client=mock_client)
        
        results = hydrator.hydrate([event])
        
        assert len(results) == 1
        result = results[0]
        
        assert result.narrative == "A cool story"
        assert event.narrative is None
        assert event is not result

    @patch('itingen.hydrators.ai.images.GeminiClient')
    def test_image_hydrator_immutability(self, mock_client_cls):
        # Create valid image bytes for post-processing
        from PIL import Image
        import io
        img = Image.new('RGB', (100, 100), color='blue')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)

        mock_client = mock_client_cls.return_value
        mock_client.generate_image_with_gemini.return_value = img_bytes.getvalue()

        # We need a cache mock because ImageHydrator uses cache for file path
        with patch('itingen.hydrators.ai.images.AiCache') as mock_cache_cls:
            mock_cache = mock_cache_cls.return_value
            # It will try to get from cache first (return None), then set, then get path
            mock_cache.get_image_path.side_effect = [None, "/path/to/image.png"]
            
            event = Event(event_heading="Visit Paris", location="Paris")
            
            from itingen.hydrators.ai.images import ImageHydrator
            hydrator = ImageHydrator(client=mock_client, cache=mock_cache)
            
            results = hydrator.hydrate([event])
            
            assert len(results) == 1
            result = results[0]

            assert result.image_path == "/path/to/image.png"
            assert event.image_path is None
            assert event is not result

    def test_transition_hydrator_immutability(self):
        e1 = Event(kind="drive", location="A")
        e2 = Event(kind="airport_buffer", location="Airport")
        events = [e1, e2]

        from itingen.pipeline.transitions_logic import TransitionHydrator
        from itingen.pipeline.nz_transitions import create_nz_transition_registry

        registry = create_nz_transition_registry()
        hydrator = TransitionHydrator(registry)

        results = hydrator.hydrate(events)

        assert len(results) == 2
        # e1 is first, no previous event, so no transition usually (or maybe None)
        # e2 should have transition from e1

        result_e2 = results[1]
        assert result_e2.transition_from_prev is not None

        # Original should be unchanged
        assert e2.transition_from_prev is None
        assert e2 is not result_e2

    def test_wrapup_hydrator_immutability(self):
        e1 = Event(event_heading="Event 1", time_local="10:00")
        e2 = Event(event_heading="Event 2", time_local="12:00")
        events = [e1, e2]
        
        from itingen.pipeline.timing import WrapUpHydrator
        hydrator = WrapUpHydrator()
        
        results = hydrator.hydrate(events)
        
        assert len(results) == 2
        result_e1 = results[0]
        
        # e1 should look ahead to e2
        assert result_e1.wrap_up_time == "12:00"
        
        # Original should be unchanged
        assert getattr(e1, "wrap_up_time", None) is None
        assert e1 is not result_e1

    def test_emotional_annotation_hydrator_immutability(self):
        e1 = Event(kind="flight_departure", event_heading="Fly away")
        
        from itingen.pipeline.annotations import EmotionalAnnotationHydrator
        hydrator = EmotionalAnnotationHydrator()
        
        results = hydrator.hydrate([e1])
        
        assert len(results) == 1
        result = results[0]
        
        assert result.emotional_triggers is not None
        assert e1.emotional_triggers is None
        assert e1 is not result

    @patch('itingen.hydrators.ai.banner.GeminiClient')
    def test_banner_hydrator_immutability(self, mock_client_cls):
        # Create valid image bytes for post-processing
        from PIL import Image
        import io
        img = Image.new('RGB', (100, 100), color='blue')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)

        mock_client = mock_client_cls.return_value
        mock_client.generate_image_with_gemini.return_value = img_bytes.getvalue()

        from itingen.rendering.timeline import TimelineDay
        # TimelineDay is a dataclass
        day = TimelineDay(
            date_str="2023-01-01",
            day_header="Day 1",
            events=[]
        )

        with patch('itingen.hydrators.ai.banner.AiCache') as mock_cache_cls:
            mock_cache = mock_cache_cls.return_value
            # Simulate cache miss on first call, then return path on second call (after set)
            from pathlib import Path
            expected_path = Path("/path/to/banner.png")
            mock_cache.get_image_path.side_effect = [None, expected_path]

            from itingen.hydrators.ai.banner import BannerImageHydrator
            hydrator = BannerImageHydrator(client=mock_client, cache=mock_cache)

            results = hydrator.hydrate([day])

            assert len(results) == 1
            result = results[0]

            assert result.banner_image_path == str(expected_path)
            assert day.banner_image_path is None
            assert day is not result

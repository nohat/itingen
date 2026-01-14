"""Tests for the Pipeline Orchestrator."""

import pytest
from typing import Any, Dict, List

from itingen.core.base import BaseProvider, BaseHydrator, BaseEmitter
from itingen.core.domain.events import Event
from itingen.pipeline.orchestrator import PipelineOrchestrator
from itingen.pipeline.transitions import TransitionRegistry


class MockProvider(BaseProvider[Event]):
    """Mock provider for testing."""
    
    def __init__(self, events: List[Event] = None, venues: Dict[str, Any] = None, config: Dict[str, Any] = None):
        self._events = events or []
        self._venues = venues or {}
        self._config = config or {}
    
    def get_events(self) -> List[Event]:
        return self._events
    
    def get_venues(self) -> Dict[str, Any]:
        return self._venues
    
    def get_config(self) -> Dict[str, Any]:
        return self._config


class MockHydrator(BaseHydrator[Event]):
    """Mock hydrator that adds a prefix to event descriptions."""
    
    def __init__(self, prefix: str = "Hydrated: "):
        self.prefix = prefix
        self.call_count = 0
    
    def hydrate(self, items: List[Event], context=None) -> List[Event]:
        self.call_count += 1
        for item in items:
            if item.description:
                item.description = self.prefix + item.description
        return items


class MockEmitter(BaseEmitter[Event]):
    """Mock emitter that writes to a dict instead of files."""
    
    def __init__(self):
        self.outputs = {}
    
    def emit(self, itinerary: List[Event], output_path: str) -> bool:
        # Instead of writing files, store in dict
        self.outputs[output_path] = len(itinerary)
        return True


class FailingProvider(BaseProvider[Event]):
    """Provider that always fails."""
    
    def get_events(self) -> List[Event]:
        raise RuntimeError("Provider failure")
    
    def get_venues(self) -> Dict[str, Any]:
        return {}
    
    def get_config(self) -> Dict[str, Any]:
        return {}


class FailingHydrator(BaseHydrator[Event]):
    """Hydrator that always fails."""
    
    def hydrate(self, items: List[Event]) -> List[Event]:
        raise RuntimeError("Hydrator failure")


class FailingEmitter(BaseEmitter[Event]):
    """Emitter that always fails."""
    
    def emit(self, itinerary: List[Event], output_path: str) -> bool:
        raise RuntimeError("Emitter failure")


@pytest.fixture
def sample_events():
    """Create sample events for testing."""
    return [
        Event(event_heading="Event 1", description="Test event 1"),
        Event(event_heading="Event 2", description="Test event 2"),
    ]


@pytest.fixture
def sample_provider(sample_events):
    """Create a sample provider."""
    return MockProvider(
        events=sample_events,
        venues={"venue1": {"name": "Venue 1"}},
        config={"trip": {"name": "Test Trip"}}
    )


def test_orchestrator_with_transition_registry(sample_provider):
    """Test orchestrator with a transition registry."""
    registry = TransitionRegistry()
    orchestrator = PipelineOrchestrator(sample_provider, transition_registry=registry)
    assert orchestrator.transition_registry == registry


def test_orchestrator_add_transition_registry(sample_provider):
    """Test adding a transition registry via method."""
    registry = TransitionRegistry()
    orchestrator = PipelineOrchestrator(sample_provider)
    result = orchestrator.set_transition_registry(registry)
    
    assert result == orchestrator
    assert orchestrator.transition_registry == registry


    """Test orchestrator initialization."""
    orchestrator = PipelineOrchestrator(sample_provider)
    assert orchestrator.provider == sample_provider
    assert orchestrator.hydrators == []
    assert orchestrator.emitters == []


def test_orchestrator_add_components(sample_provider):
    """Test adding components to the orchestrator."""
    hydrator = MockHydrator()
    emitter = MockEmitter()
    
    orchestrator = PipelineOrchestrator(sample_provider)
    result = orchestrator.add_hydrator(hydrator).add_emitter(emitter)
    
    # Should return self for chaining
    assert result == orchestrator
    assert len(orchestrator.hydrators) == 1
    assert len(orchestrator.emitters) == 1


def test_orchestrator_execute_success(sample_provider):
    """Test successful pipeline execution."""
    hydrator = MockHydrator()
    emitter = MockEmitter()
    
    orchestrator = PipelineOrchestrator(sample_provider, [hydrator], [emitter])
    result = orchestrator.execute()
    
    # Check that hydrator was called
    assert hydrator.call_count == 1
    
    # Check that events were hydrated
    assert all(e.description.startswith("Hydrated: ") for e in result)
    
    # Check that emitter was called
    assert len(emitter.outputs) == 1
    # Check that output_0 is in the keys (not necessarily the exact path)
    assert any("output_0" in path for path in emitter.outputs.keys())
    assert emitter.outputs[list(emitter.outputs.keys())[0]] == 2  # Number of events


def test_orchestrator_execute_multiple_hydrators(sample_provider):
    """Test pipeline with multiple hydrators."""
    hydrator1 = MockHydrator("H1: ")
    hydrator2 = MockHydrator("H2: ")
    emitter = MockEmitter()
    
    orchestrator = PipelineOrchestrator(
        sample_provider,
        [hydrator1, hydrator2],
        [emitter]
    )
    result = orchestrator.execute()
    
    # Check that both hydrators were called
    assert hydrator1.call_count == 1
    assert hydrator2.call_count == 1
    
    # Check that events were hydrated by both
    for e in result:
        assert e.description.startswith("H2: H1: ")


def test_orchestrator_execute_no_emitters(sample_provider):
    """Test that execution fails with no emitters."""
    orchestrator = PipelineOrchestrator(sample_provider)
    
    with pytest.raises(ValueError, match="No emitters configured"):
        orchestrator.execute()


def test_orchestrator_execute_provider_failure():
    """Test handling of provider failure."""
    provider = FailingProvider()
    orchestrator = PipelineOrchestrator(provider)
    
    with pytest.raises(RuntimeError, match="Provider failed"):
        orchestrator.execute()


def test_orchestrator_execute_hydrator_failure(sample_provider):
    """Test handling of hydrator failure."""
    hydrator = FailingHydrator()
    orchestrator = PipelineOrchestrator(sample_provider, [hydrator])
    
    with pytest.raises(RuntimeError, match="Hydrator 0 .* failed"):
        orchestrator.execute()


def test_orchestrator_execute_emitter_failure(sample_provider):
    """Test handling of emitter failure."""
    emitter = FailingEmitter()
    orchestrator = PipelineOrchestrator(sample_provider, emitters=[emitter])
    
    with pytest.raises(RuntimeError, match="Emitter 0 .* failed"):
        orchestrator.execute()


def test_orchestrator_validate_empty():
    """Test validation of empty orchestrator."""
    orchestrator = PipelineOrchestrator(None)
    issues = orchestrator.validate()
    
    assert "No provider configured" in issues
    assert "No emitters configured - pipeline will not generate output" in issues


def test_orchestrator_validate_valid(sample_provider):
    """Test validation of properly configured orchestrator."""
    hydrator = MockHydrator()
    emitter = MockEmitter()
    
    orchestrator = PipelineOrchestrator(sample_provider, [hydrator], [emitter])
    issues = orchestrator.validate()
    
    assert len(issues) == 0


def test_orchestrator_execute_with_output_dir(sample_provider, tmp_path):
    """Test execution with custom output directory."""
    emitter = MockEmitter()
    orchestrator = PipelineOrchestrator(sample_provider, emitters=[emitter])
    
    orchestrator.execute(output_dir=tmp_path)
    
    # Check that output path includes the custom directory
    assert any(str(tmp_path) in path for path in emitter.outputs.keys())


def test_orchestrator_execute_multiple_emitters(sample_provider):
    """Test execution with multiple emitters."""
    emitter1 = MockEmitter()
    emitter2 = MockEmitter()
    
    orchestrator = PipelineOrchestrator(
        sample_provider,
        emitters=[emitter1, emitter2]
    )
    orchestrator.execute()
    
    # Both emitters should have been called
    assert len(emitter1.outputs) == 1
    assert len(emitter2.outputs) == 1
    assert emitter1.outputs != emitter2.outputs  # Different output paths


def test_pipeline_context_creation():
    """Test that PipelineContext can be created with venues and config."""
    from itingen.core.base import PipelineContext
    from itingen.core.domain.venues import Venue

    venues = {"venue1": Venue(venue_id="venue1", canonical_name="Test Venue")}
    config = {"theme": "dark", "max_images": 5}

    context = PipelineContext(venues=venues, config=config)

    assert context.venues == venues
    assert context.config == config


class ContextCapturingHydrator(BaseHydrator[Event]):
    """Mock hydrator that captures the context parameter."""
    
    def __init__(self):
        self.captured_context = None
        self.call_count = 0
    
    def hydrate(self, items: List[Event], context=None) -> List[Event]:
        self.call_count += 1
        self.captured_context = context
        return items


def test_orchestrator_passes_context_to_hydrators(sample_provider):
    """Test that PipelineContext is passed to hydrators during execution."""
    from itingen.core.domain.venues import Venue
    
    # Create a hydrator that captures the context
    capturing_hydrator = ContextCapturingHydrator()
    
    # Create venues and config that should be in the context
    venues = {"test-venue": Venue(venue_id="test-venue", canonical_name="Test Venue")}
    config = {"test_config": "test_value"}
    
    # Set up provider to return our test data
    sample_provider._venues = venues
    sample_provider._config = config
    
    orchestrator = PipelineOrchestrator(
        sample_provider,
        hydrators=[capturing_hydrator],
        emitters=[MockEmitter()]  # Add emitter so orchestrator can execute
    )
    
    # Execute the pipeline
    orchestrator.execute()
    
    # Verify the hydrator was called and received the context
    assert capturing_hydrator.call_count == 1
    assert capturing_hydrator.captured_context is not None
    assert capturing_hydrator.captured_context.venues == venues
    assert capturing_hydrator.captured_context.config == config

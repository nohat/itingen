"""Tests for the Pipeline Orchestrator."""

import pytest
from pathlib import Path
from typing import Any, Dict, List

from itingen.core.base import BaseProvider, BaseHydrator, BaseEmitter
from itingen.core.domain.events import Event
from itingen.pipeline.orchestrator import PipelineOrchestrator


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
    
    def hydrate(self, items: List[Event]) -> List[Event]:
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


def test_orchestrator_init(sample_provider):
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
    
    result = orchestrator.execute(output_dir=tmp_path)
    
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
    result = orchestrator.execute()
    
    # Both emitters should have been called
    assert len(emitter1.outputs) == 1
    assert len(emitter2.outputs) == 1
    assert emitter1.outputs != emitter2.outputs  # Different output paths

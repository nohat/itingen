"""Core Pipeline Orchestrator for the SPE (Source-Pipeline-Emitter) model.

AIDEV-NOTE: This is the central coordinator that manages the flow from Provider
through a sequence of Hydrators to Emitters. It implements the SPE lifecycle.
"""

from typing import List, Generic, TypeVar, Optional, Dict, Any
from pathlib import Path

from itingen.core.base import BaseProvider, BaseHydrator, BaseEmitter, PipelineContext
from itingen.core.domain.venues import Venue
from itingen.pipeline.transitions import TransitionRegistry

T = TypeVar("T")  # The domain model type (e.g., Event or Itinerary)


class PipelineOrchestrator(Generic[T]):
    """Orchestrates the flow of data through the SPE pipeline.
    
    The orchestrator:
    1. Loads raw data using a Provider
    2. Passes it through a sequence of Hydrators for enrichment
    3. Sends the final result to one or more Emitters for output
    """
    
    def __init__(
        self,
        provider: BaseProvider[T],
        hydrators: Optional[List[BaseHydrator[T]]] = None,
        emitters: Optional[List[BaseEmitter[T]]] = None,
        transition_registry: Optional[TransitionRegistry] = None,
    ):
        """Initialize the orchestrator with components.
        
        Args:
            provider: The data provider (Source)
            hydrators: List of hydrators to apply in order (Pipeline)
            emitters: List of emitters to generate output (Target)
            transition_registry: Optional registry for event transitions
        """
        self.provider = provider
        self.hydrators = hydrators or []
        self.emitters = emitters or []
        self.transition_registry = transition_registry
        self.venues: Dict[str, Venue] = {}
        self.config: Dict[str, Any] = {}
    
    def set_transition_registry(self, registry: TransitionRegistry) -> "PipelineOrchestrator[T]":
        """Set the transition registry for the pipeline.
        
        Returns:
            Self for method chaining
        """
        self.transition_registry = registry
        return self
    
    def add_hydrator(self, hydrator: BaseHydrator[T]) -> "PipelineOrchestrator[T]":
        """Add a hydrator to the pipeline.
        
        Returns:
            Self for method chaining
        """
        self.hydrators.append(hydrator)
        return self
    
    def add_emitter(self, emitter: BaseEmitter[T]) -> "PipelineOrchestrator[T]":
        """Add an emitter to the pipeline.
        
        Returns:
            Self for method chaining
        """
        self.emitters.append(emitter)
        return self
    
    def execute(self, output_dir: Optional[Path] = None) -> List[T]:
        """Execute the complete SPE pipeline.
        
        Args:
            output_dir: Base directory for emitters to write output
            
        Returns:
            The fully hydrated data after all enrichments
            
        Raises:
            ValueError: If no emitters are configured
            RuntimeError: If any component fails
        """
        # Source Stage: Load raw data
        try:
            events = self.provider.get_events()
            # Load venues and config
            self.venues = self.provider.get_venues()
            self.config = self.provider.get_config()
        except Exception as e:
            raise RuntimeError(f"Provider failed to load data: {e}") from e
        
        # Pipeline Stage: Apply hydrators in sequence
        current_data = events
        context = PipelineContext(venues=self.venues, config=self.config)
        for i, hydrator in enumerate(self.hydrators):
            try:
                current_data = hydrator.hydrate(current_data, context)
            except Exception as e:
                raise RuntimeError(f"Hydrator {i} ({type(hydrator).__name__}) failed: {e}") from e
        
        # Emitter Stage: Generate output
        if not self.emitters:
            raise ValueError("No emitters configured - nothing to output")
        
        if output_dir is None:
            output_dir = Path.cwd()
        
        results = []
        for i, emitter in enumerate(self.emitters):
            try:
                # Determine output path for this emitter
                emitter_path = str(output_dir / f"output_{i}")
                actual_path = emitter.emit(current_data, emitter_path)
                results.append(actual_path)
            except Exception as e:
                raise RuntimeError(f"Emitter {i} ({type(emitter).__name__}) failed: {e}") from e
        
        return current_data
    
    def validate(self) -> List[str]:
        """Validate the pipeline configuration.
        
        Returns:
            List of validation warnings/errors
        """
        issues = []
        
        # Check provider
        if self.provider is None:
            issues.append("No provider configured")
        
        # Check hydrators
        for i, hydrator in enumerate(self.hydrators):
            if not isinstance(hydrator, BaseHydrator):
                issues.append(f"Hydrator {i} is not a BaseHydrator")
        
        # Check emitters
        if not self.emitters:
            issues.append("No emitters configured - pipeline will not generate output")
        
        for i, emitter in enumerate(self.emitters):
            if not isinstance(emitter, BaseEmitter):
                issues.append(f"Emitter {i} is not a BaseEmitter")
        
        return issues

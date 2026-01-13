from abc import ABC, abstractmethod
from typing import Any, Dict, List, Generic, TypeVar, Optional
from dataclasses import dataclass

from itingen.core.domain.venues import Venue

T = TypeVar("T")  # The domain model type (e.g., Event or Itinerary)

@dataclass
class PipelineContext:
    """Context data passed to hydrators containing venues and configuration.
    
    This provides access to venue information and trip-level configuration
    that hydrators may need for enrichment operations.
    """
    venues: Dict[str, Venue]
    config: Dict[str, Any]

class BaseProvider(ABC, Generic[T]):
    """Abstract base class for trip data providers.
    
    AIDEV-NOTE: Providers (Sources) are responsible for loading raw data, 
    venues, and trip-level configuration into the domain models.
    """

    @abstractmethod
    def get_events(self) -> List[T]:
        """Load and return trip events."""
        raise NotImplementedError

    @abstractmethod
    def get_venues(self) -> Dict[str, Venue]:
        """Load and return venue information."""
        raise NotImplementedError

    @abstractmethod
    def get_config(self) -> Dict[str, Any]:
        """Load and return trip-level configuration."""
        raise NotImplementedError

class BaseHydrator(ABC, Generic[T]):
    """Abstract base class for itinerary enrichers (pipeline stages).
    
    AIDEV-NOTE: Hydrators (Pipeline) enrich domain models with external data 
    (Maps, Weather, AI) in a sequential, deterministic flow.
    """

    @abstractmethod
    def hydrate(self, items: List[T], context: Optional[PipelineContext] = None) -> List[T]:
        """Enrich the given items with additional data.

        Args:
            items: The list of domain objects to enrich (e.g., events or itinerary items).
            context: Optional pipeline context containing shared data such as
                venues and trip-level configuration.

        Returns:
            The list of enriched items.
        """
        raise NotImplementedError

class BaseEmitter(ABC, Generic[T]):
    """Abstract base class for itinerary output generators.
    
    AIDEV-NOTE: Emitters (Targets) transform hydrated domain models into 
    final artifacts like Markdown, PDFs, or calendars.
    """

    @abstractmethod
    def emit(self, itinerary: List[T], output_path: str) -> str:
        """Write the itinerary to the specified output format/path.
        
        Returns:
            The path to the generated artifact.
        """
        raise NotImplementedError

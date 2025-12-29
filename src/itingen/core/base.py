from abc import ABC, abstractmethod
from typing import Any, Dict, List, Generic, TypeVar

T = TypeVar("T")  # The domain model type (e.g., Event or Itinerary)

class BaseProvider(ABC, Generic[T]):
    """Abstract base class for trip data providers."""

    @abstractmethod
    def get_events(self) -> List[T]:
        """Load and return trip events."""
        pass

    @abstractmethod
    def get_venues(self) -> Dict[str, Any]:
        """Load and return venue information."""
        pass

    @abstractmethod
    def get_config(self) -> Dict[str, Any]:
        """Load and return trip-level configuration."""
        pass

class BaseHydrator(ABC, Generic[T]):
    """Abstract base class for itinerary enrichers (pipeline stages)."""

    @abstractmethod
    def hydrate(self, items: List[T]) -> List[T]:
        """Enrich the given items with additional data."""
        pass

class BaseEmitter(ABC, Generic[T]):
    """Abstract base class for itinerary output generators."""

    @abstractmethod
    def emit(self, itinerary: List[T], output_path: str) -> bool:
        """Write the itinerary to the specified output format/path."""
        pass

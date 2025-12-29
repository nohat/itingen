"""Itingen: Generic Trip Itinerary Generation System.

A modular, local-first system for generating optimized travel itineraries
based on the Source-Pipeline-Emitter (SPE) model.
"""

from itingen.core.base import BaseProvider, BaseHydrator, BaseEmitter
from itingen.core.domain.events import Event
from itingen.core.domain.venues import Venue
from itingen.pipeline.orchestrator import PipelineOrchestrator
from itingen.providers.file_provider import LocalFileProvider

__version__ = "0.1.0"
__all__ = [
    "BaseProvider",
    "BaseHydrator", 
    "BaseEmitter",
    "Event",
    "Venue",
    "PipelineOrchestrator",
    "LocalFileProvider",
]
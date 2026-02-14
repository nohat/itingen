"""AI-powered transition hydrator using Gemini API.

This hydrator generates contextually-aware transition descriptions between
itinerary events using the Gemini API with prompt engineering and caching.
"""

from typing import List, Optional
from itingen.core.base import BaseHydrator
from itingen.core.domain.events import Event
from itingen.integrations.ai.gemini import GeminiClient
from itingen.integrations.ai.transition_prompts import (
    TRANSITION_STYLE_TEMPLATE,
    TRANSITION_PROMPT_TEMPLATE,
)
from itingen.hydrators.ai.cache import AiCache


class GeminiTransitionHydrator(BaseHydrator[Event]):
    """Hydrator that generates AI-powered transition descriptions between events.
    
    Uses Gemini to create contextually rich, engaging transition narratives
    that consider event types, locations, timing, and trip-specific context.
    
    This replaces hardcoded pattern-matching with dynamic AI generation,
    enabling trip-agnostic transitions that adapt to any event combination.
    """
    
    def __init__(
        self, 
        client: GeminiClient,
        cache: Optional[AiCache] = None,
        style_template: Optional[str] = None,
        prompt_template: Optional[str] = None
    ):
        """Initialize the Gemini transition hydrator.
        
        Args:
            client: GeminiClient instance for API calls.
            cache: Optional AiCache for caching generated transitions.
            style_template: Optional custom style guidance for prompts.
            prompt_template: Optional custom prompt template.
        """
        self.client = client
        self.cache = cache
        self.style_template = style_template or TRANSITION_STYLE_TEMPLATE
        self.prompt_template = prompt_template or TRANSITION_PROMPT_TEMPLATE
    
    def hydrate(self, items: List[Event], context=None) -> List[Event]:
        """Add AI-generated transition descriptions to events.
        
        Args:
            items: List of events to process.
            context: Optional context (unused).
            
        Returns:
            List of events with transition_from_prev populated.
        """
        if not items:
            return []
        
        new_items = []
        prev_ev: Optional[Event] = None
        
        for ev in items:
            updates = {}
            if prev_ev is not None:
                # Skip if already set (from source data)
                if not ev.transition_from_prev:
                    transition = self._generate_transition(prev_ev, ev)
                    if transition:
                        updates["transition_from_prev"] = transition
            
            new_ev = ev.model_copy(update=updates) if updates else ev
            new_items.append(new_ev)
            prev_ev = new_ev
        
        return new_items
    
    def _generate_transition(self, prev_ev: Event, curr_ev: Event) -> Optional[str]:
        """Generate transition using Gemini API with caching.
        
        Args:
            prev_ev: Previous event.
            curr_ev: Current event.
            
        Returns:
            Transition description string, or None if generation fails.
        """
        # Create cache key from event attributes
        payload = {
            "task": "transition",
            "prev_kind": prev_ev.kind,
            "prev_location": prev_ev.location,
            "prev_travel_to": prev_ev.travel_to,
            "prev_travel_mode": getattr(prev_ev, "travel_mode", None),
            "curr_kind": curr_ev.kind,
            "curr_location": curr_ev.location,
            "curr_travel_from": curr_ev.travel_from,
            "curr_travel_to": curr_ev.travel_to,
            "curr_travel_mode": getattr(curr_ev, "travel_mode", None),
            "curr_driver": getattr(curr_ev, "driver", None),
            "curr_parking": getattr(curr_ev, "parking", None),
            "prompt_template": self.prompt_template
        }
        
        # Check cache first
        cached_transition = None
        if self.cache:
            cached_transition = self.cache.get_text(payload)
        
        if cached_transition:
            return cached_transition
        
        # Generate with Gemini
        prompt = self._build_prompt(prev_ev, curr_ev)
        transition = self.client.generate_text(prompt)
        
        # Clean up response (remove quotes, extra whitespace)
        transition = transition.strip().strip('"\'')
        
        # Cache the result
        if self.cache:
            self.cache.set_text(payload, transition)
        
        return transition
    
    def _build_prompt(self, prev_ev: Event, curr_ev: Event) -> str:
        """Build the Gemini prompt for transition generation.
        
        Args:
            prev_ev: Previous event.
            curr_ev: Current event.
            
        Returns:
            Formatted prompt string.
        """
        return self.prompt_template.format(
            style_guidance=self.style_template,
            prev_kind=prev_ev.kind or "N/A",
            prev_location=prev_ev.location or "N/A",
            prev_travel_to=prev_ev.travel_to or "N/A",
            prev_travel_mode=getattr(prev_ev, "travel_mode", "N/A"),
            curr_kind=curr_ev.kind or "N/A",
            curr_location=curr_ev.location or "N/A",
            curr_travel_from=curr_ev.travel_from or "N/A",
            curr_travel_to=curr_ev.travel_to or "N/A",
            curr_travel_mode=getattr(curr_ev, "travel_mode", "N/A"),
            curr_driver=getattr(curr_ev, "driver", "N/A"),
            curr_parking=getattr(curr_ev, "parking", "N/A")
        )

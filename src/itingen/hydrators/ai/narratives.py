from typing import List, Optional, Dict, Any
from itingen.core.base import BaseHydrator
from itingen.core.domain.events import Event
from itingen.integrations.ai.gemini import GeminiClient
from itingen.hydrators.ai.cache import AiCache

class NarrativeHydrator(BaseHydrator[Event]):
    """Hydrator that generates AI narratives for events."""

    def __init__(self, client: GeminiClient, cache: Optional[AiCache] = None, prompt_template: Optional[str] = None):
        self.client = client
        self.cache = cache
        self.prompt_template = prompt_template or (
            "Describe the following travel event in a friendly, engaging narrative tone:\n"
            "Event: {heading}\n"
            "Kind: {kind}\n"
            "Location: {location}\n"
            "Description: {description}\n"
            "Participants: {who}\n"
        )

    def hydrate(self, items: List[Event]) -> List[Event]:
        for event in items:
            if not event.event_heading:
                continue

            payload = {
                "task": "narrative",
                "heading": event.event_heading,
                "kind": event.kind,
                "location": event.location,
                "description": event.description,
                "who": event.who,
                "prompt_template": self.prompt_template
            }

            narrative = None
            if self.cache:
                narrative = self.cache.get_text(payload)

            if not narrative:
                prompt = self.prompt_template.format(
                    heading=event.event_heading,
                    kind=event.kind or "N/A",
                    location=event.location or "N/A",
                    description=event.description or "N/A",
                    who=", ".join(event.who) if event.who else "N/A"
                )
                narrative = self.client.generate_text(prompt)
                if self.cache:
                    self.cache.set_text(payload, narrative)

            event.narrative = narrative
            
        return items

from typing import List, Optional
from itingen.core.base import BaseHydrator
from itingen.core.domain.events import Event
from itingen.integrations.ai.gemini import GeminiClient
from itingen.integrations.ai.narrative_prompts import NARRATIVE_STYLE_TEMPLATE, NARRATIVE_PROMPT_TEMPLATE
from itingen.hydrators.ai.cache import AiCache

class NarrativeHydrator(BaseHydrator[Event]):
    """Hydrator that generates AI narratives for events."""

    def __init__(self, client: GeminiClient, cache: Optional[AiCache] = None, prompt_template: Optional[str] = None, style_template: Optional[str] = None):
        self.client = client
        self.cache = cache
        self.style_template = style_template or NARRATIVE_STYLE_TEMPLATE
        self.prompt_template = prompt_template or NARRATIVE_PROMPT_TEMPLATE

    def hydrate(self, items: List[Event]) -> List[Event]:
        new_items = []
        for event in items:
            if not event.event_heading:
                new_items.append(event)
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
                    style_guidance=self.style_template,
                    heading=event.event_heading,
                    kind=event.kind or "N/A",
                    location=event.location or "N/A",
                    description=event.description or "N/A",
                    who=", ".join(event.who) if event.who else "N/A"
                )
                narrative = self.client.generate_text(prompt)
                if self.cache:
                    self.cache.set_text(payload, narrative)

            new_items.append(event.model_copy(update={"narrative": narrative}))
            
        return new_items

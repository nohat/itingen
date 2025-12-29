from typing import List, Optional
from itingen.core.base import BaseHydrator
from itingen.core.domain.events import Event
from itingen.integrations.ai.gemini import GeminiClient
from itingen.hydrators.ai.cache import AiCache

class ImageHydrator(BaseHydrator[Event]):
    """Hydrator that generates AI images for events."""

    def __init__(self, client: GeminiClient, cache: Optional[AiCache] = None, prompt_template: Optional[str] = None):
        self.client = client
        self.cache = cache
        self.prompt_template = prompt_template or (
            "A high-quality travel photograph of {location} for a {kind} event. "
            "The image should capture the atmosphere of {heading}."
        )

    def hydrate(self, items: List[Event]) -> List[Event]:
        for event in items:
            # Only generate images for events with a location
            if not event.location:
                continue

            payload = {
                "task": "image",
                "heading": event.event_heading,
                "kind": event.kind,
                "location": event.location,
                "prompt_template": self.prompt_template
            }

            image_path = None
            if self.cache:
                image_path = self.cache.get_image_path(payload)

            if not image_path:
                prompt = self.prompt_template.format(
                    heading=event.event_heading or "Travel",
                    kind=event.kind or "activity",
                    location=event.location
                )
                image_bytes = self.client.generate_image(prompt)
                if self.cache:
                    self.cache.set_image(payload, image_bytes)
                    image_path = self.cache.get_image_path(payload)

            if image_path:
                event.image_path = str(image_path)
            
        return items

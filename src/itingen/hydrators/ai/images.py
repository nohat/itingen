from typing import List, Optional
from itingen.core.base import BaseHydrator
from itingen.core.domain.events import Event
from itingen.integrations.ai.gemini import GeminiClient
from itingen.integrations.ai.image_prompts import format_thumbnail_prompt
from itingen.hydrators.ai.cache import AiCache

class ImageHydrator(BaseHydrator[Event]):
    """Hydrator that generates AI thumbnail images for events using Gemini.

    This generates 1:1 square thumbnail images in Ligne Claire style for individual events.
    For day banner images (16:9), use BannerImageHydrator instead.
    """

    def __init__(
        self,
        client: GeminiClient,
        cache: Optional[AiCache] = None,
        model: str = "gemini-2.5-flash-image"
    ):
        """Initialize the ImageHydrator.

        Args:
            client: GeminiClient for image generation
            cache: Optional AiCache for caching generated images
            model: Gemini image model to use (default: gemini-2.5-flash-image)
        """
        self.client = client
        self.cache = cache
        self.model = model

    def hydrate(self, items: List[Event]) -> List[Event]:
        new_items = []
        for event in items:
            # Only generate images for events with a location
            if not event.location:
                new_items.append(event)
                continue

            # Create cache payload
            payload = {
                "task": "thumbnail",
                "model": self.model,
                "heading": event.event_heading or "",
                "kind": event.kind or "",
                "location": event.location or "",
                "description": event.description or "",
                "travel_mode": getattr(event, "travel_mode", "") or "",
                "travel_from": getattr(event, "travel_from", "") or "",
                "travel_to": getattr(event, "travel_to", "") or "",
            }

            image_path = None
            if self.cache:
                image_path = self.cache.get_image_path(payload)

            if not image_path:
                # Generate prompt using template from scaffold POC
                prompt = format_thumbnail_prompt(
                    event_heading=event.event_heading or "Event",
                    location=event.location,
                    kind=event.kind or "activity",
                    description=event.description or "",
                    travel_mode=getattr(event, "travel_mode", "") or "",
                    travel_from=getattr(event, "travel_from", "") or "",
                    travel_to=getattr(event, "travel_to", "") or "",
                )

                # Generate image with Gemini (1:1 thumbnail)
                image_bytes = self.client.generate_image_with_gemini(
                    prompt=prompt,
                    model=self.model,
                    aspect_ratio="1:1",
                    image_size="1K"
                )

                if self.cache:
                    self.cache.set_image(payload, image_bytes)
                    image_path = self.cache.get_image_path(payload)

            if image_path:
                new_items.append(event.model_copy(update={"image_path": str(image_path)}))
            else:
                new_items.append(event)

        return new_items


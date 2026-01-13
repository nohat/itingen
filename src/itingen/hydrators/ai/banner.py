from __future__ import annotations

import os
from enum import Enum
from typing import List, Optional
from dataclasses import replace

from itingen.core.base import BaseHydrator
from itingen.integrations.ai.gemini import GeminiClient
from itingen.integrations.ai.image_prompts import format_banner_prompt
from itingen.hydrators.ai.cache import AiCache
from itingen.rendering.timeline import TimelineDay
from itingen.utils.fingerprint import compute_fingerprint
from itingen.utils.image_postprocessing import postprocess_image


class BannerCachePolicy(str, Enum):
    """Cache policy strategies for banner images."""
    STABLE_DATE = "stable_date"      # Use date only (ignore content changes)
    FINGERPRINT = "fingerprint"      # Use full fingerprint (regen on any change)
    HYBRID = "hybrid"               # Date + truncated fingerprint (balance)


class BannerImageHydrator(BaseHydrator[TimelineDay]):
    """Hydrator that generates AI banner images for days using Gemini Nano Banana Pro.

    This generates 16:9 panoramic banner images for day headers using the most
    advanced image generation model for maximum detail and instruction following.

    Cache behavior is configurable via BannerCachePolicy:
    - STABLE_DATE: Most stable during development (ignores content changes)
    - FINGERPRINT: Regenerates on any content change
    - HYBRID: Balance between stability and content awareness
    """

    def __init__(
        self,
        client: GeminiClient,
        cache: Optional[AiCache] = None,
        cache_policy: BannerCachePolicy = BannerCachePolicy.STABLE_DATE,
        model: Optional[str] = None,
        force_refresh: bool = False,
    ):
        """Initialize the BannerImageHydrator.

        Args:
            client: GeminiClient for image generation
            cache: Optional AiCache for caching generated banners
            cache_policy: Cache strategy for banner images
            model: Gemini model to use (defaults to gemini-3-pro-image-preview)
            force_refresh: Force regeneration even if cached
        """
        self.client = client
        self.cache = cache
        self.cache_policy = cache_policy
        self.model = model or os.environ.get("BANNER_MODEL", "gemini-3-pro-image-preview")
        self.force_refresh = force_refresh

    def hydrate(self, days: List[TimelineDay]) -> List[TimelineDay]:
        """Generate banner images for timeline days.

        Args:
            days: List of TimelineDay objects to enrich with banner images

        Returns:
            TimelineDay objects with banner_image_path set when available
        """
        enriched_days = []
        for day in days:
            cache_key = self._cache_key(day)
            
            # Check cache unless forcing refresh
            image_path = None
            if self.cache and not self.force_refresh:
                image_path = self.cache.get_image_path({
                    "task": "day_banner",
                    "cache_key": cache_key
                })
            
            # Generate if not cached
            if not image_path:
                prompt = self._banner_prompt(day)
                
                # Save prompt for inspection (debug mode)
                if self.cache:
                    prompt_file = self.cache.cache_dir / f"banner_{day.date_str}_prompt.txt"
                    prompt_file.write_text(prompt, encoding="utf-8")
                
                image_bytes = self.client.generate_image_with_gemini(
                    prompt=prompt,
                    model=self.model,
                    aspect_ratio="16:9",
                    image_size="2K"
                )
                
                # Apply post-processing: crop borders, ensure 16:9 aspect, optimize format
                processed_bytes = postprocess_image(
                    image_bytes,
                    target_aspect=(16, 9),
                    max_trim_percent=0.22,
                    prefer_png=True
                )
                
                if self.cache:
                    self.cache.set_image({
                        "task": "day_banner", 
                        "cache_key": cache_key
                    }, processed_bytes)
                    # Get the path we just set - don't call get_image_path again
                    cache_payload = {
                        "task": "day_banner",
                        "cache_key": cache_key
                    }
                    # For testing purposes, we'll compute the expected path
                    from itingen.utils.fingerprint import compute_fingerprint
                    fp = compute_fingerprint(cache_payload)
                    image_path = self.cache.image_cache / f"{fp}.jpg"
            
            # Create enriched day with banner path
            if image_path:
                enriched_day = replace(day, banner_image_path=str(image_path))
            else:
                enriched_day = day
                
            enriched_days.append(enriched_day)
                
        return enriched_days

    def generate(self, days: List[TimelineDay]) -> List[TimelineDay]:
        """Alias for hydrate method to match BannerGenerator protocol.
        
        This allows BannerImageHydrator to be used as a BannerGenerator
        in PDFEmitter while maintaining the hydrator interface.
        """
        return self.hydrate(days)

    def _cache_key(self, day: TimelineDay) -> str:
        """Generate cache key based on policy."""
        base_key = f"banner_{day.date_str}"
        
        if self.cache_policy == BannerCachePolicy.STABLE_DATE:
            return base_key  # Just date, ignores content changes
            
        elif self.cache_policy == BannerCachePolicy.FINGERPRINT:
            payload = self._banner_payload(day)
            fp = compute_fingerprint(payload)
            return f"{base_key}_{fp}"  # Full fingerprint
            
        elif self.cache_policy == BannerCachePolicy.HYBRID:
            # Use short fingerprint (first 8 chars) for some stability
            payload = self._banner_payload(day)
            fp = compute_fingerprint(payload)[:8]
            return f"{base_key}_{fp}"
            
        return base_key

    def _banner_payload(self, day: TimelineDay) -> dict:
        """Create payload for fingerprint calculation."""
        return {
            "task": "day_banner",
            "model": self.model,
            "date": day.date_str,
            "day_header": day.day_header,
            "hero_events": self._hero_events(day),
            "location": self._primary_location(day),
        }

    def _primary_location(self, day: TimelineDay) -> str:
        """Extract primary location from day events."""
        from collections import Counter
        
        locations = [e.location for e in day.events if getattr(e, "location", None)]
        if not locations:
            return "the destination"
        return Counter(locations).most_common(1)[0][0]

    def _hero_events(self, day: TimelineDay) -> List[str]:
        """Extract hero events for banner prompt generation."""
        hero: List[str] = []
        for e in day.events:
            heading = getattr(e, "event_heading", None)
            if heading:
                hero.append(heading)
            if len(hero) >= 3:
                break
        return hero

    def _banner_prompt(self, day: TimelineDay) -> str:
        """Generate banner image prompt for a day."""
        location = self._primary_location(day)
        hero_events = self._hero_events(day)
        supporting_details: List[str] = []

        for e in day.events:
            loc = getattr(e, "location", None)
            if loc and loc != location and loc not in supporting_details:
                supporting_details.append(loc)
            if len(supporting_details) >= 6:
                break

        return format_banner_prompt(
            date=day.date_str,
            location=location,
            hero_events=hero_events,
            supporting_details=supporting_details,
        )

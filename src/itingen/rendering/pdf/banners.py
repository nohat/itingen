from __future__ import annotations

from collections import Counter
from dataclasses import replace
from pathlib import Path
from typing import List, Optional

from itingen.integrations.ai.gemini import GeminiClient
from itingen.integrations.ai.image_prompts import format_banner_prompt
from itingen.rendering.timeline import TimelineDay
from itingen.utils.fingerprint import compute_fingerprint


class DayBannerGenerator:
    def __init__(
        self,
        client: GeminiClient,
        cache_dir: str | Path,
        model: str = "imagen-4.0-ultra-generate-001",
    ):
        self.client = client
        self.cache_dir = Path(cache_dir)
        self.banners_dir = self.cache_dir / "banners"
        self.banners_dir.mkdir(parents=True, exist_ok=True)
        self.model = model

    def generate(self, days: List[TimelineDay]) -> List[TimelineDay]:
        enriched: List[TimelineDay] = []
        for day in days:
            banner_path = self._get_or_create_banner(day)
            if banner_path is None:
                enriched.append(day)
            else:
                # TimelineDay is a dataclass; preserve immutability expectations by returning a new instance
                enriched.append(replace(day, banner_image_path=str(banner_path)))
        return enriched

    def _get_or_create_banner(self, day: TimelineDay) -> Optional[Path]:
        payload = self._banner_payload(day)
        key = compute_fingerprint(payload)
        banner_path = self.banners_dir / f"{key}.png"

        if banner_path.exists():
            return banner_path

        prompt = self._banner_prompt(day)
        image_bytes = self.client.generate_image_with_imagen(
            prompt=prompt,
            model=self.model,
            aspect_ratio="16:9",
        )
        banner_path.write_bytes(image_bytes)
        return banner_path

    def _banner_payload(self, day: TimelineDay) -> dict:
        return {
            "task": "day_banner",
            "model": self.model,
            "date": day.date_str,
            "day_header": day.day_header,
            "hero_events": self._hero_events(day),
            "location": self._primary_location(day),
        }

    def _primary_location(self, day: TimelineDay) -> str:
        locations = [e.location for e in day.events if getattr(e, "location", None)]
        if not locations:
            return "the destination"
        return Counter(locations).most_common(1)[0][0]

    def _hero_events(self, day: TimelineDay) -> List[str]:
        hero: List[str] = []
        for e in day.events:
            heading = getattr(e, "event_heading", None)
            if heading:
                hero.append(heading)
            if len(hero) >= 3:
                break
        return hero

    def _banner_prompt(self, day: TimelineDay) -> str:
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

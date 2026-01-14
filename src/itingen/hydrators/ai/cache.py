import json
from pathlib import Path
from typing import Optional
from itingen.utils.fingerprint import compute_fingerprint

class AiCache:
    """Cache for AI-generated content (text and images)."""

    def __init__(self, cache_dir: str | Path):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.text_cache = self.cache_dir / "text"
        self.image_cache = self.cache_dir / "images"
        self.text_cache.mkdir(exist_ok=True)
        self.image_cache.mkdir(exist_ok=True)

    def get_text(self, payload: dict) -> Optional[str]:
        """Retrieve cached text based on payload fingerprint."""
        key = compute_fingerprint(payload)
        cache_file = self.text_cache / f"{key}.txt"
        if cache_file.exists():
            return cache_file.read_text(encoding="utf-8")
        return None

    def set_text(self, payload: dict, text: str):
        """Cache text content."""
        key = compute_fingerprint(payload)
        cache_file = self.text_cache / f"{key}.txt"
        cache_file.write_text(text, encoding="utf-8")
        
        # Also save the payload for debugging
        payload_file = self.text_cache / f"{key}.json"
        with open(payload_file, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, sort_keys=True)

    def get_image_path(self, payload: dict) -> Optional[Path]:
        """Retrieve path to cached image based on payload fingerprint."""
        key = compute_fingerprint(payload)
        cache_file = self.image_cache / f"{key}.png"
        if cache_file.exists():
            return cache_file
        return None

    def set_image(self, payload: dict, image_data: bytes):
        """Cache image content."""
        key = compute_fingerprint(payload)
        cache_file = self.image_cache / f"{key}.png"
        cache_file.write_bytes(image_data)
        
        # Also save the payload for debugging
        payload_file = self.image_cache / f"{key}.json"
        with open(payload_file, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, sort_keys=True)

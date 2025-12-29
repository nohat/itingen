from typing import Optional
import os
from google import genai
from google.genai import types

class GeminiClient:
    """Client for interacting with Google Gemini AI."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-2.0-flash-exp"):
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment or provided to client")
        
        self.client = genai.Client(api_key=self.api_key)
        self.model = model

    def generate_text(self, prompt: str) -> str:
        """Generate text using Gemini."""
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt
        )
        return response.text

    def generate_image(self, prompt: str, aspect_ratio: str = "1:1") -> bytes:
        """Generate an image using Imagen via Gemini."""
        # Note: In the new genai SDK, image generation might be via a different method
        # or specific models. For now, we'll implement the pattern.
        # This is a placeholder for the actual Imagen 3 call.
        response = self.client.models.generate_image(
            model="imagen-3.0-generate-002",
            prompt=prompt,
            config=types.GenerateImageConfig(
                number_of_images=1,
                aspect_ratio=aspect_ratio,
                add_watermark=False
            )
        )
        return response.generated_images[0].image_bytes

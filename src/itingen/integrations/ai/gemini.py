from typing import Optional, Literal
import os
import base64
try:
    from dotenv import load_dotenv
    load_dotenv(override=True)  # Force .env file to override any existing env vars
except ImportError:
    pass  # python-dotenv not installed, fallback to environment variables only
from google import genai
from google.genai import types

class GeminiClient:
    """Client for interacting with Google Gemini AI."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-2.0-flash-exp"):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment or provided to client")

        self.client = genai.Client(api_key=self.api_key)
        self.model = model

    def generate_text(self, prompt: str) -> str:
        """Generate text using Gemini."""
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt
        )
        return response.text

    def generate_image_with_gemini(
        self,
        prompt: str,
        model: str = "gemini-2.5-flash-image",
        aspect_ratio: Literal["1:1", "16:9", "9:16", "4:3", "3:4"] = "1:1",
        image_size: str = "1K"
    ) -> bytes:
        """Generate an image using Gemini models (gemini-2.5-flash-image, gemini-3-pro-image-preview).

        This uses the generate_content endpoint with IMAGE response modality.

        Args:
            prompt: Image generation prompt
            model: Gemini image model (e.g., "gemini-2.5-flash-image")
            aspect_ratio: Image aspect ratio (1:1, 16:9, 9:16, 4:3, 3:4) - now properly enforced via ImageConfig
            image_size: Image size ("1K" = 1024x1024, "2K" = 2048x2048)

        Returns:
            Image bytes (PNG format)

        AIDEV-NOTE: Fixed banner aspect ratio issue by adding image_config=types.ImageConfig() to match scaffold POC.
        Previously only appended aspect ratio to prompt text, but Gemini models need structured ImageConfig for proper enforcement.
        """
        # Add aspect ratio and size to prompt (imageConfig not yet supported for Gemini)
        enhanced_prompt = f"{prompt} {aspect_ratio} aspect ratio."
        if image_size != "1K":
            enhanced_prompt += f" {image_size} resolution."

        # Use generate_content with IMAGE modality for Gemini models
        config = types.GenerateContentConfig(
            response_modalities=["IMAGE"],
            image_config=types.ImageConfig(
                aspect_ratio=aspect_ratio,
                image_size=image_size,
            )
        )

        response = self.client.models.generate_content(
            model=model,
            contents=enhanced_prompt,
            config=config
        )

        # Extract image bytes from response
        # Try multiple extraction methods (scaffold POC uses this approach)
        image_bytes = None

        if hasattr(response, 'parts') and response.parts:
            for part in response.parts:
                # Method 1: inline_data
                if hasattr(part, 'inline_data') and part.inline_data:
                    image_bytes = part.inline_data.data
                    break
                # Method 2: as_image() (PIL Image)
                if hasattr(part, 'as_image'):
                    try:
                        from io import BytesIO
                        pil_image = part.as_image()
                        buffer = BytesIO()
                        pil_image.save(buffer, format='PNG')
                        image_bytes = buffer.getvalue()
                        break
                    except Exception:
                        pass

        if not image_bytes:
            raise ValueError("Failed to extract image data from Gemini response")

        # Handle base64 encoding if needed
        if isinstance(image_bytes, str):
            image_bytes = base64.b64decode(image_bytes)

        return image_bytes

    def generate_image_with_imagen(
        self,
        prompt: str,
        model: str = "imagen-4.0-ultra-generate-001",
        aspect_ratio: Literal["1:1", "16:9", "9:16", "4:3", "3:4"] = "16:9"
    ) -> bytes:
        """Generate an image using Imagen models (imagen-4.0-ultra-generate-001).

        This uses the generate_images endpoint specifically for Imagen.

        Args:
            prompt: Image generation prompt
            model: Imagen model (e.g., "imagen-4.0-ultra-generate-001")
            aspect_ratio: Image aspect ratio (1:1, 16:9, 9:16, 4:3, 3:4)

        Returns:
            Image bytes (PNG format)
        """
        config = types.GenerateImagesConfig(
            aspect_ratio=aspect_ratio,
            person_generation="dont_allow"  # Scaffold POC sets this
        )

        response = self.client.models.generate_images(
            model=model,
            prompt=prompt,
            config=config
        )

        if not response.generated_images:
            raise ValueError("No images generated by Imagen")

        # Extract image bytes from first generated image
        image_obj = response.generated_images[0]

        # The response structure is: GeneratedImage -> Image -> image_bytes
        if hasattr(image_obj, 'image'):
            img = image_obj.image
            if hasattr(img, 'image_bytes'):
                return img.image_bytes

        raise ValueError("Failed to extract image data from Imagen response")

    def generate_image(self, prompt: str) -> bytes:
        """Generate an image using Imagen via Gemini (legacy method for backward compatibility).

        DEPRECATED: Use generate_image_with_gemini() or generate_image_with_imagen() instead.
        """
        # Default to Gemini image generation for thumbnails
        return self.generate_image_with_gemini(prompt, aspect_ratio="1:1")

import pytest
from unittest.mock import patch, MagicMock
from itingen.integrations.ai.gemini import GeminiClient
from google.genai import types


class TestGeminiClient:
    """Unit tests for GeminiClient."""

    @patch("itingen.integrations.ai.gemini.os.environ.get")
    @patch("itingen.integrations.ai.gemini.genai.Client")
    def test_init_with_api_key_provided(self, mock_genai, mock_env):
        """Initialize with provided API key."""
        mock_env.return_value = "env-key"
        
        client = GeminiClient(api_key="provided-key", model="custom-model")
        
        assert client.api_key == "provided-key"
        assert client.model == "custom-model"
        mock_genai.assert_called_once_with(api_key="provided-key")

    @patch("itingen.integrations.ai.gemini.os.environ.get")
    @patch("itingen.integrations.ai.gemini.genai.Client")
    def test_init_with_env_api_key(self, mock_genai, mock_env):
        """Initialize with API key from environment."""
        mock_env.return_value = "env-api-key"
        
        client = GeminiClient()  # No API key provided
        
        assert client.api_key == "env-api-key"
        assert client.model == "gemini-2.0-flash-exp"  # Default model
        mock_genai.assert_called_once_with(api_key="env-api-key")

    @patch("itingen.integrations.ai.gemini.os.environ.get")
    def test_init_no_api_key_raises_error(self, mock_env):
        """Raise error when no API key available."""
        mock_env.return_value = None
        
        with pytest.raises(ValueError, match="GOOGLE_API_KEY not found"):
            GeminiClient()

    @patch("itingen.integrations.ai.gemini.os.environ.get")
    @patch("itingen.integrations.ai.gemini.genai.Client")
    def test_generate_text_success(self, mock_genai, mock_env):
        """Generate text successfully."""
        mock_env.return_value = "env-key"
        mock_client = MagicMock()
        mock_genai.return_value = mock_client
        
        # Mock response
        mock_response = MagicMock()
        mock_response.text = "Generated text response"
        mock_client.models.generate_content.return_value = mock_response
        
        client = GeminiClient()
        result = client.generate_text("Test prompt")
        
        assert result == "Generated text response"
        mock_client.models.generate_content.assert_called_once_with(
            model="gemini-2.0-flash-exp",
            contents="Test prompt"
        )

    @patch("itingen.integrations.ai.gemini.os.environ.get")
    @patch("itingen.integrations.ai.gemini.genai.Client")
    def test_generate_image_with_gemini_success(self, mock_genai, mock_env):
        """Generate thumbnail image using Gemini model."""
        mock_env.return_value = "env-key"
        mock_client = MagicMock()
        mock_genai.return_value = mock_client
        
        # Mock response structure for Gemini IMAGE modality
        mock_response = MagicMock()
        mock_part = MagicMock()
        mock_part.inline_data.data = b"fake-gemini-image"
        mock_response.parts = [mock_part]
        mock_client.models.generate_content.return_value = mock_response
        
        client = GeminiClient()
        result = client.generate_image_with_gemini("Test prompt")
        
        assert result == b"fake-gemini-image"
        
        # Verify call arguments
        mock_client.models.generate_content.assert_called_once()
        args, kwargs = mock_client.models.generate_content.call_args
        assert kwargs["model"] == "gemini-2.5-flash-image"
        assert "IMAGE" in kwargs["config"].response_modalities
        assert "Test prompt" in kwargs["contents"]

    @patch("itingen.integrations.ai.gemini.os.environ.get")
    @patch("itingen.integrations.ai.gemini.genai.Client")
    def test_generate_image_with_imagen_success(self, mock_genai, mock_env):
        """Generate banner image using Imagen model."""
        mock_env.return_value = "env-key"
        mock_client = MagicMock()
        mock_genai.return_value = mock_client
        
        # Mock response structure for Imagen
        mock_response = MagicMock()
        mock_image = MagicMock()
        mock_inner_image = MagicMock()
        mock_inner_image.image_bytes = b"fake-imagen-image"
        mock_image.image = mock_inner_image
        mock_response.generated_images = [mock_image]
        mock_client.models.generate_images.return_value = mock_response
        
        client = GeminiClient()
        result = client.generate_image_with_imagen("Test banner prompt")
        
        assert result == b"fake-imagen-image"
        
        # Verify call arguments
        mock_client.models.generate_images.assert_called_once()
        args, kwargs = mock_client.models.generate_images.call_args
        assert kwargs["model"] == "imagen-4.0-ultra-generate-001"
        assert kwargs["prompt"] == "Test banner prompt"
        assert kwargs["config"].aspect_ratio == "16:9"

    @patch("itingen.integrations.ai.gemini.os.environ.get")
    @patch("itingen.integrations.ai.gemini.genai.Client")
    def test_generate_image_legacy_fallback(self, mock_genai, mock_env):
        """Test legacy generate_image calls generate_image_with_gemini."""
        mock_env.return_value = "env-key"
        client = GeminiClient()
        
        # Mock the new method
        with patch.object(client, 'generate_image_with_gemini') as mock_new_method:
            mock_new_method.return_value = b"legacy-image"
            
            result = client.generate_image("Legacy prompt")
            
            assert result == b"legacy-image"
            mock_new_method.assert_called_once_with("Legacy prompt", aspect_ratio="1:1")

    @patch("itingen.integrations.ai.gemini.os.environ.get")
    @patch("itingen.integrations.ai.gemini.genai.Client")
    def test_generate_image_gemini_extraction_failure(self, mock_genai, mock_env):
        """Raise error when Gemini response has no image data."""
        mock_env.return_value = "env-key"
        mock_client = MagicMock()
        mock_genai.return_value = mock_client
        
        # Response with no parts
        mock_response = MagicMock()
        mock_response.parts = []
        mock_client.models.generate_content.return_value = mock_response
        
        client = GeminiClient()
        
        with pytest.raises(ValueError, match="Failed to extract image data"):
            client.generate_image_with_gemini("Test prompt")

    @patch("itingen.integrations.ai.gemini.os.environ.get")
    @patch("itingen.integrations.ai.gemini.genai.Client")
    def test_generate_image_imagen_extraction_failure(self, mock_genai, mock_env):
        """Raise error when Imagen response has no images."""
        mock_env.return_value = "env-key"
        mock_client = MagicMock()
        mock_genai.return_value = mock_client
        
        # Response with empty generated_images
        mock_response = MagicMock()
        mock_response.generated_images = []
        mock_client.models.generate_images.return_value = mock_response
        
        client = GeminiClient()
        
        with pytest.raises(ValueError, match="No images generated"):
            client.generate_image_with_imagen("Test prompt")

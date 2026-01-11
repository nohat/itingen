import pytest
from unittest.mock import patch, MagicMock
from itingen.integrations.ai.gemini import GeminiClient


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
    def test_init_default_model(self, mock_genai, mock_env):
        """Use default model when not specified."""
        mock_env.return_value = "env-key"
        
        client = GeminiClient(api_key="test-key")
        
        assert client.model == "gemini-2.0-flash-exp"

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
    def test_generate_text_with_custom_model(self, mock_genai, mock_env):
        """Generate text with custom model."""
        mock_env.return_value = "env-key"
        mock_client = MagicMock()
        mock_genai.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.text = "Custom model response"
        mock_client.models.generate_content.return_value = mock_response
        
        client = GeminiClient(model="custom-model")
        result = client.generate_text("Test prompt")
        
        assert result == "Custom model response"
        mock_client.models.generate_content.assert_called_once_with(
            model="custom-model",
            contents="Test prompt"
        )

    @patch("itingen.integrations.ai.gemini.os.environ.get")
    @patch("itingen.integrations.ai.gemini.genai.Client")
    def test_generate_text_api_exception(self, mock_genai, mock_env):
        """Handle API exceptions during text generation."""
        mock_env.return_value = "env-key"
        mock_client = MagicMock()
        mock_genai.return_value = mock_client
        
        mock_client.models.generate_content.side_effect = Exception("API Error")
        
        client = GeminiClient()
        
        with pytest.raises(Exception, match="API Error"):
            client.generate_text("Test prompt")

    @patch("itingen.integrations.ai.gemini.os.environ.get")
    @patch("itingen.integrations.ai.gemini.genai.Client")
    def test_generate_image_success(self, mock_genai, mock_env):
        """Generate image successfully."""
        mock_env.return_value = "env-key"
        mock_client = MagicMock()
        mock_genai.return_value = mock_client
        
        # Mock response
        mock_response = MagicMock()
        mock_image = MagicMock()
        mock_image.image_bytes = b"fake-image-data"
        mock_response.generated_images = [mock_image]
        mock_client.models.generate_images.return_value = mock_response
        
        client = GeminiClient()
        result = client.generate_image("Test image prompt", "16:9")
        
        assert result == b"fake-image-data"
        mock_client.models.generate_images.assert_called_once_with(
            model="imagen-3.0-generate-002",
            prompt="Test image prompt",
            aspect_ratio="16:9",
            number_of_images=1
        )

    @patch("itingen.integrations.ai.gemini.os.environ.get")
    @patch("itingen.integrations.ai.gemini.genai.Client")
    def test_generate_image_default_aspect_ratio(self, mock_genai, mock_env):
        """Generate image with default aspect ratio."""
        mock_env.return_value = "env-key"
        mock_client = MagicMock()
        mock_genai.return_value = mock_client
        
        mock_response = MagicMock()
        mock_image = MagicMock()
        mock_image.image_bytes = b"fake-image-data"
        mock_response.generated_images = [mock_image]
        mock_client.models.generate_images.return_value = mock_response
        
        client = GeminiClient()
        result = client.generate_image("Test prompt")
        
        assert result == b"fake-image-data"
        mock_client.models.generate_images.assert_called_once_with(
            model="imagen-3.0-generate-002",
            prompt="Test prompt",
            aspect_ratio="1:1",  # Default aspect ratio
            number_of_images=1
        )

    @patch("itingen.integrations.ai.gemini.os.environ.get")
    @patch("itingen.integrations.ai.gemini.genai.Client")
    def test_generate_image_api_exception(self, mock_genai, mock_env):
        """Handle API exceptions during image generation."""
        mock_env.return_value = "env-key"
        mock_client = MagicMock()
        mock_genai.return_value = mock_client
        
        mock_client.models.generate_images.side_effect = Exception("Image API Error")
        
        client = GeminiClient()
        
        with pytest.raises(Exception, match="Image API Error"):
            client.generate_image("Test prompt")

    @patch("itingen.integrations.ai.gemini.os.environ.get")
    @patch("itingen.integrations.ai.gemini.genai.Client")
    def test_generate_image_response_with_no_images(self, mock_genai, mock_env):
        """Handle response with no generated images."""
        mock_env.return_value = "env-key"
        mock_client = MagicMock()
        mock_genai.return_value = mock_client
        
        # Mock response with no images
        mock_response = MagicMock()
        mock_response.generated_images = []
        mock_client.models.generate_images.return_value = mock_response
        
        client = GeminiClient()
        
        with pytest.raises(IndexError):
            client.generate_image("Test prompt")

    @patch("itingen.integrations.ai.gemini.os.environ.get")
    @patch("itingen.integrations.ai.gemini.genai.Client")
    def test_client_attributes(self, mock_genai, mock_env):
        """Test client has expected attributes."""
        mock_env.return_value = "env-key"
        mock_client = MagicMock()
        mock_genai.return_value = mock_client
        
        client = GeminiClient(api_key="test-key", model="test-model")
        
        assert hasattr(client, 'api_key')
        assert hasattr(client, 'client')
        assert hasattr(client, 'model')
        assert hasattr(client, 'generate_text')
        assert hasattr(client, 'generate_image')

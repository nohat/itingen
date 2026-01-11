import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, Mock
from itingen.integrations.weather.weatherspark import WeatherSparkClient


@pytest.fixture
def temp_cache_dir():
    """Provide a temporary cache directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def sample_weatherspark_html():
    """Sample HTML from WeatherSpark (simplified)."""
    return """
    <html>
    <body>
        <p>The daily average high temperature typically ranges from 45°F to 72°F</p>
        <p>Over the course of the day there is a 20% chance of precipitation</p>
        <p>The sky is mostly clear with wind speed typically ranges from 5 mph to 12 mph</p>
    </body>
    </html>
    """


def test_cache_directory_creation(temp_cache_dir):
    """Test that cache directory is created if it doesn't exist."""
    cache_path = Path(temp_cache_dir) / "weather_cache"
    client = WeatherSparkClient(cache_dir=str(cache_path))

    assert cache_path.exists()
    assert client.cache_dir == cache_path


def test_cache_hit_returns_cached_data(temp_cache_dir):
    """Test that cached weather data is returned without network call."""
    client = WeatherSparkClient(cache_dir=temp_cache_dir)

    # Pre-populate cache
    cache_key = client._get_cache_key("Auckland, New Zealand", "2025-01-15")
    cache_file = Path(temp_cache_dir) / f"{cache_key}.json"
    cached_data = {
        "high_temp_f": 72,
        "low_temp_f": 58,
        "conditions": "partly cloudy",
        "precip_chance_pct": 15
    }
    cache_file.write_text(json.dumps(cached_data))

    # Should return cached data without network call
    result = client.get_typical_weather("Auckland, New Zealand", "2025-01-15")

    assert result == cached_data


@patch('itingen.integrations.weather.weatherspark.requests.get')
def test_weather_fetch_and_parse(mock_get, temp_cache_dir, sample_weatherspark_html):
    """Test fetching and parsing weather data from WeatherSpark."""
    # Mock HTTP response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = sample_weatherspark_html
    mock_get.return_value = mock_response

    client = WeatherSparkClient(cache_dir=temp_cache_dir)
    result = client.get_typical_weather("Auckland, New Zealand", "2025-01-15")

    # Verify parsed data
    assert result is not None
    assert result["high_temp_f"] == 72
    assert result["low_temp_f"] == 45
    assert result["conditions"] == "mostly clear"
    assert result["precip_chance_pct"] == 20

    # Verify cache was written
    cache_key = client._get_cache_key("Auckland, New Zealand", "2025-01-15")
    cache_file = Path(temp_cache_dir) / f"{cache_key}.json"
    assert cache_file.exists()


@patch('itingen.integrations.weather.weatherspark.requests.get')
def test_unknown_location_returns_none(mock_get, temp_cache_dir):
    """Test that unknown locations return None."""
    client = WeatherSparkClient(cache_dir=temp_cache_dir)

    # Should not make network call for completely unknown location
    result = client.get_typical_weather("UnknownCity123", "2025-01-15")

    assert result is None
    mock_get.assert_not_called()


@patch('itingen.integrations.weather.weatherspark.requests.get')
def test_network_failure_returns_none(mock_get, temp_cache_dir):
    """Test that network failures return None gracefully."""
    mock_get.side_effect = Exception("Network error")

    client = WeatherSparkClient(cache_dir=temp_cache_dir)
    result = client.get_typical_weather("Auckland, New Zealand", "2025-01-15")

    assert result is None


@patch('itingen.integrations.weather.weatherspark.requests.get')
def test_http_error_returns_none(mock_get, temp_cache_dir):
    """Test that HTTP errors return None."""
    mock_response = Mock()
    mock_response.status_code = 404
    mock_get.return_value = mock_response

    client = WeatherSparkClient(cache_dir=temp_cache_dir)
    result = client.get_typical_weather("Auckland, New Zealand", "2025-01-15")

    assert result is None


def test_location_inference_auckland():
    """Test location inference for Auckland variations."""
    client = WeatherSparkClient()

    assert client._infer_place_key("Auckland, New Zealand") == "auckland"
    assert client._infer_place_key("auckland") == "auckland"
    assert client._infer_place_key("AKL Airport") == "auckland"


def test_location_inference_queenstown():
    """Test location inference for Queenstown variations."""
    client = WeatherSparkClient()

    assert client._infer_place_key("Queenstown, New Zealand") == "queenstown"
    assert client._infer_place_key("queenstown") == "queenstown"
    assert client._infer_place_key("ZQN") == "queenstown"


def test_location_inference_unknown():
    """Test location inference returns None for unknown locations."""
    client = WeatherSparkClient()

    assert client._infer_place_key("Mars Colony") is None
    assert client._infer_place_key("") is None

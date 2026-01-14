"""Tests for TripConfig class."""
import pytest
import yaml
from itingen.config.trip_config import TripConfig


@pytest.fixture
def trip_dir(tmp_path):
    """Create a temporary trip directory structure."""
    trip = tmp_path / "test_trip"
    events_dir = trip / "events"
    venues_dir = trip / "venues"
    prompts_dir = trip / "prompts"
    events_dir.mkdir(parents=True)
    venues_dir.mkdir(parents=True)
    prompts_dir.mkdir(parents=True)

    # Create config.yaml
    config = {
        "trip_name": "Test Adventure 2026",
        "timezone": "America/Los_Angeles",
        "people": [
            {"name": "Alice", "slug": "alice"},
            {"name": "Bob", "slug": "bob"}
        ]
    }
    with open(trip / "config.yaml", "w") as f:
        yaml.dump(config, f)

    return trip


def test_trip_config_init(trip_dir):
    """Test TripConfig initialization with valid directory."""
    config = TripConfig(trip_name="test_trip", trips_dir=trip_dir.parent)
    assert config.trip_name == "test_trip"
    assert config.trip_dir == trip_dir


def test_trip_config_init_invalid_directory(tmp_path):
    """Test TripConfig raises error when trip directory does not exist."""
    with pytest.raises(ValueError, match="Trip directory not found"):
        TripConfig(trip_name="nonexistent_trip", trips_dir=tmp_path)


def test_trip_config_init_missing_config_file(tmp_path):
    """Test TripConfig raises error when config.yaml is missing."""
    trip = tmp_path / "trip_without_config"
    trip.mkdir()

    with pytest.raises(FileNotFoundError, match="Trip config not found"):
        TripConfig(trip_name="trip_without_config", trips_dir=tmp_path)


def test_trip_config_get_events_dir(trip_dir):
    """Test get_events_dir returns correct path."""
    config = TripConfig(trip_name="test_trip", trips_dir=trip_dir.parent)
    events_dir = config.get_events_dir()
    assert events_dir == trip_dir / "events"
    assert events_dir.exists()


def test_trip_config_get_venues_dir(trip_dir):
    """Test get_venues_dir returns correct path."""
    config = TripConfig(trip_name="test_trip", trips_dir=trip_dir.parent)
    venues_dir = config.get_venues_dir()
    assert venues_dir == trip_dir / "venues"
    assert venues_dir.exists()


def test_trip_config_get_prompts_dir(trip_dir):
    """Test get_prompts_dir returns correct path."""
    config = TripConfig(trip_name="test_trip", trips_dir=trip_dir.parent)
    prompts_dir = config.get_prompts_dir()
    assert prompts_dir == trip_dir / "prompts"
    assert prompts_dir.exists()


def test_trip_config_get_travelers(trip_dir):
    """Test get_travelers returns list of travelers."""
    config = TripConfig(trip_name="test_trip", trips_dir=trip_dir.parent)
    travelers = config.get_travelers()
    assert len(travelers) == 2
    assert travelers[0] == {"name": "Alice", "slug": "alice"}
    assert travelers[1] == {"name": "Bob", "slug": "bob"}


def test_trip_config_default_trips_dir(tmp_path, monkeypatch):
    """Test TripConfig uses default trips/ directory when not specified."""
    # Change working directory to tmp_path
    monkeypatch.chdir(tmp_path)

    # Create trips/test_trip structure
    trip = tmp_path / "trips" / "test_trip"
    trip.mkdir(parents=True)
    config_data = {"trip_name": "Test Trip", "people": []}
    with open(trip / "config.yaml", "w") as f:
        yaml.dump(config_data, f)

    config = TripConfig(trip_name="test_trip")
    assert config.trip_dir == trip


def test_trip_config_get_timezone(trip_dir):
    """Test get_timezone returns timezone from config."""
    config = TripConfig(trip_name="test_trip", trips_dir=trip_dir.parent)
    timezone = config.get_timezone()
    assert timezone == "America/Los_Angeles"


def test_trip_config_get_timezone_default(tmp_path):
    """Test get_timezone returns None when not in config."""
    trip = tmp_path / "trip_no_tz"
    trip.mkdir()
    config_data = {"trip_name": "Test Trip", "people": []}
    with open(trip / "config.yaml", "w") as f:
        yaml.dump(config_data, f)

    config = TripConfig(trip_name="trip_no_tz", trips_dir=tmp_path)
    timezone = config.get_timezone()
    assert timezone is None


def test_trip_config_get_trip_name_from_config(trip_dir):
    """Test get_trip_name_from_config returns trip name from config."""
    config = TripConfig(trip_name="test_trip", trips_dir=trip_dir.parent)
    trip_name = config.get_trip_name_from_config()
    assert trip_name == "Test Adventure 2026"


def test_trip_config_get_method(trip_dir):
    """Test get method for accessing arbitrary config values."""
    config = TripConfig(trip_name="test_trip", trips_dir=trip_dir.parent)

    # Test getting existing value
    assert config.get("timezone") == "America/Los_Angeles"

    # Test getting non-existent value with default
    assert config.get("nonexistent", "default_value") == "default_value"

    # Test getting non-existent value without default
    assert config.get("nonexistent") is None

import pytest
from pydantic import ValidationError
from itingen.core.domain.events import Event
from itingen.core.domain.venues import Venue, VenueMetadata

def test_event_typo_raises_validation_error():
    """Test that a typo in Event field name now raises a ValidationError."""
    with pytest.raises(ValidationError, match="Possible typo detected: field 'event_heding' is very similar to existing field 'event_heading'"):
        Event(event_heding="Typo here")

def test_venue_typo_raises_validation_error():
    """Test that a typo in Venue field name now raises a ValidationError."""
    metadata = VenueMetadata(created_at="2025-01-01T00:00:00Z", updated_at="2025-01-01T00:00:00Z")
    with pytest.raises(ValidationError, match="Possible typo detected: field 'addres' is very similar to existing field 'address'"):
        Venue(
            venue_id="test-venue",
            canonical_name="Test Venue",
            metadata=metadata,
            addres="Typo here"
        )

def test_venue_metadata_now_optional():
    """Test that creating a Venue without metadata now succeeds."""
    venue = Venue(
        venue_id="test-venue",
        canonical_name="Test Venue"
    )
    assert venue.metadata is not None
    assert venue.metadata.created_at is not None
    assert venue.metadata.updated_at is not None

def test_venue_metadata_fields_now_have_defaults():
    """Test that VenueMetadata has defaults for created_at and updated_at."""
    meta = VenueMetadata()
    assert meta.created_at is not None
    assert meta.updated_at is not None

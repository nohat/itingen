import pytest
from itingen.core.domain.events import Event
from itingen.rendering.markdown import MarkdownEmitter
from itingen.rendering.pdf import PDFEmitter

@pytest.fixture
def sample_itinerary():
    return [
        Event(
            event_heading="Flight to Tokyo",
            kind="flight",
            location="SFO",
            time_utc="2025-01-01T10:00:00Z",
            who=["Alice", "Bob"],
            description="United Airlines UA837"
        ),
        Event(
            event_heading="Hotel Check-in",
            kind="lodging",
            location="Park Hyatt Tokyo",
            travel_to="Take the Airport Limousine Bus"
        )
    ]

def test_markdown_emitter(sample_itinerary, tmp_path):
    output_path = tmp_path / "itinerary.md"
    emitter = MarkdownEmitter()

    result_path = emitter.emit(sample_itinerary, str(output_path))

    assert result_path == str(output_path)
    assert output_path.exists()
    content = output_path.read_text()
    assert "# Trip Itinerary" in content
    # Events are bullet points, not H2 headers (dates are H2)
    assert "Flight to Tokyo" in content
    assert "United Airlines UA837" in content
    assert "Take the Airport Limousine Bus" in content

def test_markdown_emitter_with_images(tmp_path):
    """Test that markdown emitter includes image references when image_path is present."""
    # Create actual image file so existence check passes
    image_dir = tmp_path / "cache" / "images"
    image_dir.mkdir(parents=True)
    image_file = image_dir / "temple_thumbnail.png"
    image_file.write_bytes(b"fake image content")

    itinerary = [
        Event(
            event_heading="Visit Temple",
            kind="activity",
            location="Senso-ji Temple",
            time_utc="2025-01-01T09:00:00Z",
            description="Ancient Buddhist temple",
            image_path=str(image_file)
        ),
        Event(
            event_heading="Lunch Break",
            kind="meal",
            location="Ramen Shop",
            time_utc="2025-01-01T12:00:00Z",
            # No image_path - should not render image
        )
    ]

    output_path = tmp_path / "itinerary_with_images.md"
    emitter = MarkdownEmitter()

    result_path = emitter.emit(itinerary, str(output_path))

    assert result_path == str(output_path)
    assert output_path.exists()
    content = output_path.read_text()

    # Check that image reference is included for events with image_path
    assert f"![Visit Temple]({image_file})" in content

    # Check that events without image_path don't have image references
    assert "Lunch Break" in content
    assert "![Lunch Break]" not in content

def test_markdown_emitter_skips_nonexistent_images(tmp_path):
    """Test that markdown emitter skips images when image_path points to non-existent file."""
    itinerary = [
        Event(
            event_heading="Visit Museum",
            kind="activity",
            location="National Museum",
            time_utc="2025-01-01T10:00:00Z",
            description="Art exhibition",
            image_path="cache/images/nonexistent.png"  # File doesn't exist
        ),
        Event(
            event_heading="Dinner",
            kind="meal",
            location="Restaurant",
            time_utc="2025-01-01T18:00:00Z",
        )
    ]

    output_path = tmp_path / "itinerary_no_images.md"
    emitter = MarkdownEmitter()

    result_path = emitter.emit(itinerary, str(output_path))

    assert result_path == str(output_path)
    assert output_path.exists()
    content = output_path.read_text()

    # Check that non-existent image is NOT rendered
    assert "![Visit Museum](cache/images/nonexistent.png)" not in content
    # But the event itself should still be present
    assert "Visit Museum" in content
    assert "Art exhibition" in content

def test_pdf_emitter(sample_itinerary, tmp_path):
    output_path = tmp_path / "itinerary.pdf"
    emitter = PDFEmitter()

    result_path = emitter.emit(sample_itinerary, str(output_path))

    assert result_path == str(output_path)
    assert output_path.exists()
    # Basic check that file is not empty and has PDF header
    with open(output_path, "rb") as f:
        header = f.read(4)
        assert header == b"%PDF"

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
    itinerary = [
        Event(
            event_heading="Visit Temple",
            kind="activity",
            location="Senso-ji Temple",
            time_utc="2025-01-01T09:00:00Z",
            description="Ancient Buddhist temple",
            image_path="cache/images/temple_thumbnail.png"
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

    assert output_path.exists()
    content = output_path.read_text()

    # Check that image reference is included for events with image_path
    assert "![Visit Temple](cache/images/temple_thumbnail.png)" in content

    # Check that events without image_path don't have image references
    assert "Lunch Break" in content
    assert "![Lunch Break]" not in content

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

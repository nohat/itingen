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

"""Unit tests for PDF emitter and components."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from itingen.core.domain.events import Event
from itingen.rendering.pdf.renderer import PDFEmitter
from itingen.rendering.pdf.components import EventComponent, DayComponent, PDFComponent
from itingen.rendering.pdf.themes import PDFTheme
from itingen.rendering.timeline import TimelineDay

@pytest.fixture
def mock_theme():
    """Create a mock theme for testing."""
    return PDFTheme(
        colors={"primary": "#FF0000", "text": "#000000"},
        fonts={"heading": "Arial", "body": "Arial"},
    )

@pytest.fixture
def mock_fpdf():
    """Create a mock FPDF instance."""
    pdf = MagicMock()
    # Mock layout properties
    pdf.epw = 190  # Effective page width
    pdf.w = 210    # Page width (A4)
    pdf.h = 297    # Page height (A4)
    pdf.l_margin = 10
    pdf.r_margin = 10
    pdf.b_margin = 10
    pdf.get_y.return_value = 20
    pdf.get_x.return_value = 10
    return pdf

class TestEventComponent:
    """Test EventComponent rendering logic."""

    def test_render_basic_event(self, mock_fpdf, mock_theme):
        """Test rendering a simple event without image."""
        component = EventComponent()
        event = Event(
            event_heading="Test Event",
            time_local="10:00",
            location="Test Location",
            description="Test Description"
        )

        component.render(mock_fpdf, mock_theme, event)

        # Verify calls
        # Should set font for time
        mock_fpdf.set_font.assert_any_call("Arial", "B", 10)
        # Should render time
        mock_fpdf.cell.assert_any_call(25, 5, "10:00", ln=0)
        # Should render heading
        mock_fpdf.multi_cell.assert_any_call(190 - 25 - 4, 6, "Test Event")
        # Should NOT try to render image
        mock_fpdf.image.assert_not_called()

    def test_render_event_with_image(self, mock_fpdf, mock_theme, tmp_path):
        """Test rendering an event with a thumbnail image."""
        component = EventComponent()
        
        # Create dummy image file
        image_path = tmp_path / "thumb.png"
        image_path.write_text("fake image content")
        
        event = Event(
            event_heading="Visual Event",
            image_path=str(image_path)
        )

        component.render(mock_fpdf, mock_theme, event)

        # Verify image rendering
        mock_fpdf.image.assert_called_once()
        args, kwargs = mock_fpdf.image.call_args
        assert args[0] == str(image_path)
        assert kwargs['w'] == 35  # IMAGE_SIZE
        assert kwargs['h'] == 35

    def test_render_event_details(self, mock_fpdf, mock_theme):
        """Test rendering event details (location, who, notes)."""
        component = EventComponent()
        event = Event(
            event_heading="Detailed Event",
            location="Tokyo",
            who=["Alice", "Bob"],
            notes="Bring cash",
            narrative="It was a sunny day."
        )

        component.render(mock_fpdf, mock_theme, event)

        # Verify details rendering
        # We can't easily check exact string matches in multi_cell args if they are dynamic
        # But we can check that multi_cell was called enough times
        assert mock_fpdf.multi_cell.call_count >= 3  # Heading, Details, Narrative, Notes

class TestDayComponent:
    """Test DayComponent rendering logic."""

    def test_render_day_header(self, mock_fpdf, mock_theme):
        """Test rendering day header and basic info."""
        component = DayComponent()
        day = TimelineDay(
            date_str="2025-01-01",
            day_header="2025-01-01 (Wednesday)",
            events=[],
            wake_up_location="Hotel",
            sleep_location="Hotel"
        )

        component.render(mock_fpdf, mock_theme, day)

        # Verify page add
        mock_fpdf.add_page.assert_called()
        # Verify title
        mock_fpdf.cell.assert_any_call(0, 10, "2025-01-01 (Wednesday)", ln=True)
        # Verify wake up
        mock_fpdf.cell.assert_any_call(0, 6, "Wake up: Hotel", ln=True)
        # Verify sleep
        mock_fpdf.cell.assert_any_call(0, 10, "Sleep at: Hotel", ln=True, align="R")

    def test_render_day_with_banner(self, mock_fpdf, mock_theme, tmp_path):
        """Test rendering day with banner image."""
        component = DayComponent()
        
        banner_path = tmp_path / "banner.png"
        banner_path.write_text("fake banner")
        
        day = TimelineDay(
            date_str="2025-01-01",
            day_header="Day 1",
            events=[],
            banner_image_path=str(banner_path)
        )

        component.render(mock_fpdf, mock_theme, day)

        # Verify banner image
        mock_fpdf.image.assert_called_once()
        args, kwargs = mock_fpdf.image.call_args
        assert args[0] == str(banner_path)
        assert kwargs['w'] == mock_fpdf.w

class TestPDFEmitter:
    """Test PDFEmitter orchestration."""

    @patch("itingen.rendering.pdf.renderer.FPDF")
    def test_emit_pdf_creation(self, mock_fpdf_cls, tmp_path):
        """Test that emit creates a PDF file."""
        mock_pdf = Mock()
        # Set layout properties needed for rendering
        mock_pdf.h = 297
        mock_pdf.w = 210
        mock_pdf.l_margin = 10
        mock_pdf.r_margin = 10
        mock_pdf.b_margin = 10
        mock_pdf.get_y.return_value = 20
        mock_pdf.get_x.return_value = 10
        mock_pdf.epw = 190
        
        mock_fpdf_cls.return_value = mock_pdf
        
        emitter = PDFEmitter()
        output_path = tmp_path / "output.pdf"
        
        events = [
            Event(event_heading="E1", date="2025-01-01", time_utc="2025-01-01T10:00:00Z"),
            Event(event_heading="E2", date="2025-01-02", time_utc="2025-01-02T10:00:00Z")
        ]
        
        result = emitter.emit(events, str(output_path))
        
        assert result == str(output_path)
        assert output_path.parent.exists()
        
        # Verify PDF structure calls
        # 1 title page + 2 days = 3 pages added via components
        # Note: DayComponent adds a page for each day. Title adds a page.
        assert mock_pdf.add_page.call_count >= 3 
        
        mock_pdf.output.assert_called_once_with(str(output_path))

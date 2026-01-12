"""Unit tests for PDF emitter and components."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from itingen.core.domain.events import Event
from itingen.rendering.pdf.renderer import PDFEmitter
from itingen.rendering.pdf.components import EventComponent, DayComponent
from itingen.rendering.pdf.themes import PDFTheme
from itingen.rendering.timeline import TimelineDay
from reportlab.lib.styles import getSampleStyleSheet

@pytest.fixture
def mock_theme():
    """Create a mock theme for testing."""
    return PDFTheme(
        colors={"primary": "#FF0000", "text": "#000000"},
        fonts={"heading": "Arial", "body": "Arial"},
    )

@pytest.fixture
def mock_styles():
    """Create mock ReportLab styles."""
    styles = getSampleStyleSheet()
    # Add custom styles that components expect
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib import colors
    
    styles.add(ParagraphStyle(
        name="itinerary_body",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=colors.black,
        alignment=TA_LEFT,
    ))
    
    styles.add(ParagraphStyle(
        name="event_details",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        textColor=colors.gray,
        alignment=TA_LEFT,
    ))
    
    styles.add(ParagraphStyle(
        name="day_header",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=colors.black,
        alignment=TA_LEFT,
    ))
    
    return styles

class TestEventComponent:
    """Test EventComponent rendering logic."""

    def test_render_basic_event(self, mock_styles, mock_theme):
        """Test rendering a simple event without image."""
        component = EventComponent()
        story = []
        event = Event(
            event_heading="Test Event",
            time_local="10:00",
            location="Test Location",
            description="Test Description"
        )

        component.render(story, mock_styles, mock_theme, event)

        # Verify story has content
        assert len(story) > 0
        # Should have a KeepTogether with table
        from reportlab.platypus import KeepTogether
        assert any(isinstance(item, KeepTogether) for item in story)

    def test_render_event_with_image(self, mock_styles, mock_theme, tmp_path):
        """Test rendering an event with a thumbnail image."""
        component = EventComponent()
        story = []
        
        # Create dummy image file (need a real image for ReportLab)
        from PIL import Image as PILImage
        image_path = tmp_path / "thumb.png"
        img = PILImage.new('RGB', (100, 100), color='red')
        img.save(image_path)
        
        event = Event(
            event_heading="Visual Event",
            image_path=str(image_path)
        )

        component.render(story, mock_styles, mock_theme, event)

        # Verify story has content
        assert len(story) > 0

    def test_render_event_details(self, mock_styles, mock_theme):
        """Test rendering event details (location, who, notes)."""
        component = EventComponent()
        story = []
        event = Event(
            event_heading="Detailed Event",
            location="Tokyo",
            who=["Alice", "Bob"],
            notes="Bring cash",
            narrative="It was a sunny day."
        )

        component.render(story, mock_styles, mock_theme, event)

        # Verify story has content
        assert len(story) > 0

class TestDayComponent:
    """Test DayComponent rendering logic."""

    def test_render_day_header(self, mock_styles, mock_theme):
        """Test rendering day header and basic info."""
        component = DayComponent()
        story = []
        day = TimelineDay(
            date_str="2025-01-01",
            day_header="2025-01-01 (Wednesday)",
            events=[],
            wake_up_location="Hotel",
            sleep_location="Hotel"
        )

        component.render(story, mock_styles, mock_theme, day)

        # Verify story has content (PageBreak, title, wake/sleep info)
        assert len(story) > 0
        from reportlab.platypus import PageBreak
        assert any(isinstance(item, PageBreak) for item in story)

    def test_render_day_with_banner(self, mock_styles, mock_theme, tmp_path):
        """Test rendering day with banner image."""
        component = DayComponent()
        story = []
        
        # Create real image for ReportLab
        from PIL import Image as PILImage
        banner_path = tmp_path / "banner.png"
        img = PILImage.new('RGB', (800, 450), color='blue')
        img.save(banner_path)
        
        day = TimelineDay(
            date_str="2025-01-01",
            day_header="Day 1",
            events=[],
            banner_image_path=str(banner_path)
        )

        component.render(story, mock_styles, mock_theme, day)

        # Verify story has content including image
        assert len(story) > 0
        from reportlab.platypus import Image
        assert any(isinstance(item, Image) for item in story)

class TestPDFEmitter:
    """Test PDFEmitter orchestration."""

    def test_emit_pdf_creation(self, tmp_path):
        """Test that emit creates a PDF file."""
        emitter = PDFEmitter()
        output_path = tmp_path / "output.pdf"
        
        events = [
            Event(event_heading="E1", date="2025-01-01", time_utc="2025-01-01T10:00:00Z"),
            Event(event_heading="E2", date="2025-01-02", time_utc="2025-01-02T10:00:00Z")
        ]
        
        result = emitter.emit(events, str(output_path))
        
        assert result == str(output_path)
        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_emit_uses_banner_generator_when_provided(self, tmp_path):
        """Test that a banner generator can enrich TimelineDay objects before rendering."""
        # Prepare timeline days as if they came from TimelineProcessor
        day1 = TimelineDay(date_str="2025-01-01", day_header="Day 1", events=[])
        day2 = TimelineDay(date_str="2025-01-02", day_header="Day 2", events=[])
        timeline_days = [day1, day2]

        # Create real images
        from PIL import Image as PILImage
        banner1 = tmp_path / "banner_1.png"
        banner2 = tmp_path / "banner_2.png"
        img1 = PILImage.new('RGB', (800, 450), color='red')
        img2 = PILImage.new('RGB', (800, 450), color='green')
        img1.save(banner1)
        img2.save(banner2)

        banner_generator = Mock()

        def _generate(days):
            days[0].banner_image_path = str(banner1)
            days[1].banner_image_path = str(banner2)
            return days

        banner_generator.generate.side_effect = _generate

        emitter = PDFEmitter(banner_generator=banner_generator)
        emitter.timeline_processor.process = Mock(return_value=timeline_days)

        output_path = tmp_path / "output.pdf"
        events = [
            Event(event_heading="E1", date="2025-01-01", time_utc="2025-01-01T10:00:00Z"),
            Event(event_heading="E2", date="2025-01-02", time_utc="2025-01-02T10:00:00Z"),
        ]

        result = emitter.emit(events, str(output_path))

        banner_generator.generate.assert_called_once()
        assert output_path.exists()
        assert output_path.stat().st_size > 0

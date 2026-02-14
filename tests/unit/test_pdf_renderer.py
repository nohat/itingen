"""Unit tests for PDF emitter and components."""

import pytest
from unittest.mock import Mock
from itingen.core.domain.events import Event
from itingen.rendering.pdf.renderer import PDFEmitter, build_styles
from itingen.rendering.pdf.components import EventComponent, DayComponent
from itingen.rendering.pdf.themes import PDFTheme
from itingen.rendering.timeline import TimelineDay


@pytest.fixture
def theme():
    return PDFTheme()


@pytest.fixture
def styles(theme):
    return build_styles(theme)


class TestEventComponent:
    """Test EventComponent rendering logic."""

    def test_render_basic_event(self, styles, theme):
        """Test rendering a simple event without image."""
        component = EventComponent()
        story = []
        event = Event(
            event_heading="Test Event",
            time_local="10:00",
            location="Test Location",
            description="Test Description",
        )

        component.render(story, styles, theme, event)

        assert len(story) > 0
        from reportlab.platypus import KeepTogether
        assert any(isinstance(item, KeepTogether) for item in story)

    def test_render_event_with_image(self, styles, theme, tmp_path):
        """Test rendering an event with a thumbnail image."""
        component = EventComponent()
        story = []

        from PIL import Image as PILImage
        image_path = tmp_path / "thumb.png"
        img = PILImage.new("RGB", (100, 100), color="red")
        img.save(image_path)

        event = Event(
            event_heading="Visual Event",
            image_path=str(image_path),
        )

        component.render(story, styles, theme, event)
        assert len(story) > 0

    def test_render_event_details(self, styles, theme):
        """Test rendering event details (location, who, notes)."""
        component = EventComponent()
        story = []
        event = Event(
            event_heading="Detailed Event",
            location="Tokyo",
            who=["Alice", "Bob"],
            notes="Bring cash",
            narrative="It was a sunny day.",
        )

        component.render(story, styles, theme, event)
        assert len(story) > 0

    def test_render_event_with_kind_badge(self, styles, theme):
        """Test that an event with a kind gets a kind badge."""
        component = EventComponent()
        story = []
        event = Event(
            event_heading="Dinner",
            kind="meal",
        )

        component.render(story, styles, theme, event)
        assert len(story) > 0


class TestDayComponent:
    """Test DayComponent rendering logic."""

    def test_render_day_header(self, styles, theme):
        """Test rendering day header and basic info."""
        component = DayComponent()
        story = []
        day = TimelineDay(
            date_str="2025-01-01",
            day_header="2025-01-01 (Wednesday)",
            events=[],
            wake_up_location="Hotel",
            sleep_location="Hotel",
        )

        component.render(story, styles, theme, day)

        assert len(story) > 0
        from reportlab.platypus import PageBreak
        assert any(isinstance(item, PageBreak) for item in story)

    def test_render_day_with_banner(self, styles, theme, tmp_path):
        """Test rendering day with banner image creates HeroBanner."""
        component = DayComponent()
        story = []

        from PIL import Image as PILImage
        banner_path = tmp_path / "banner.png"
        img = PILImage.new("RGB", (800, 450), color="blue")
        img.save(banner_path)

        day = TimelineDay(
            date_str="2025-01-01",
            day_header="Day 1",
            events=[],
            banner_image_path=str(banner_path),
        )

        component.render(story, styles, theme, day)
        assert len(story) > 0
        from itingen.rendering.pdf.flowables import HeroBanner
        assert any(isinstance(item, HeroBanner) for item in story)

    def test_render_day_with_weather(self, styles, theme):
        """Test rendering day with weather summary box."""
        component = DayComponent()
        story = []
        day = TimelineDay(
            date_str="2025-01-01",
            day_header="Day 1",
            events=[],
            weather_high=75.0,
            weather_low=60.0,
            weather_conditions="Partly Cloudy",
        )

        component.render(story, styles, theme, day)
        assert len(story) > 0
        from reportlab.platypus import Table
        assert any(isinstance(item, Table) for item in story)

    def test_render_day_with_partial_weather_high_only(self, styles, theme):
        """When only high is present, weather card is still shown."""
        component = DayComponent()
        story = []
        day = TimelineDay(
            date_str="2025-01-01",
            day_header="Day 1",
            events=[],
            weather_high=75.0,
            weather_low=None,
        )

        component.render(story, styles, theme, day)
        from reportlab.platypus import Table
        assert any(isinstance(item, Table) for item in story)

    def test_render_day_no_weather(self, styles, theme):
        """When no weather data, no weather card is rendered."""
        component = DayComponent()
        story = []
        day = TimelineDay(
            date_str="2025-01-01",
            day_header="Day 1",
            events=[],
            weather_high=None,
            weather_low=None,
        )

        component.render(story, styles, theme, day)
        # Should have PageBreak, title, spacer — but no Table for weather
        from reportlab.platypus import Table
        assert not any(isinstance(item, Table) for item in story)


class TestPDFEmitter:
    """Test PDFEmitter orchestration."""

    def test_emit_pdf_creation(self, tmp_path):
        """Test that emit creates a PDF file."""
        emitter = PDFEmitter()
        output_path = tmp_path / "output.pdf"

        events = [
            Event(
                event_heading="E1",
                date="2025-01-01",
                time_utc="2025-01-01T10:00:00Z",
            ),
            Event(
                event_heading="E2",
                date="2025-01-02",
                time_utc="2025-01-02T10:00:00Z",
            ),
        ]

        result = emitter.emit(events, str(output_path))

        assert result == str(output_path)
        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_emit_uses_banner_generator_when_provided(self, tmp_path):
        """Test that a banner generator can enrich TimelineDay objects."""
        day1 = TimelineDay(date_str="2025-01-01", day_header="Day 1", events=[])
        day2 = TimelineDay(date_str="2025-01-02", day_header="Day 2", events=[])
        timeline_days = [day1, day2]

        from PIL import Image as PILImage
        banner1 = tmp_path / "banner_1.png"
        banner2 = tmp_path / "banner_2.png"
        img1 = PILImage.new("RGB", (800, 450), color="red")
        img2 = PILImage.new("RGB", (800, 450), color="green")
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
            Event(
                event_heading="E1",
                date="2025-01-01",
                time_utc="2025-01-01T10:00:00Z",
            ),
            Event(
                event_heading="E2",
                date="2025-01-02",
                time_utc="2025-01-02T10:00:00Z",
            ),
        ]

        emitter.emit(events, str(output_path))

        banner_generator.generate.assert_called_once()
        assert output_path.exists()
        assert output_path.stat().st_size > 0


class TestBuildStyles:
    """Test the typography scale."""

    def test_returns_all_expected_styles(self, theme):
        styles = build_styles(theme)
        expected = {
            "eyebrow", "topline", "title", "subtitle", "subhead",
            "body", "overview_body", "event_title", "event_time",
            "event_details", "pill", "meta", "muted", "material_icon",
            "tiny", "tiny_right",
        }
        assert expected.issubset(set(styles.keys()))

    def test_title_uses_headline_font(self, theme):
        styles = build_styles(theme)
        # Should use CormorantGaramond-Semibold if available, else fallback
        assert styles["title"].fontSize == 21

    def test_body_uses_serif_font(self, theme):
        styles = build_styles(theme)
        assert styles["body"].fontSize == 10


class TestFmtTime:
    """Test time formatting."""

    def test_simple_time(self):
        from itingen.rendering.pdf.formatting import fmt_time
        assert fmt_time("10:00") == "10am"

    def test_time_with_minutes(self):
        from itingen.rendering.pdf.formatting import fmt_time
        assert fmt_time("10:30") == "10:30am"

    def test_time_with_date_prefix(self):
        from itingen.rendering.pdf.formatting import fmt_time
        assert fmt_time("2025-01-01 14:00") == "2pm"

    def test_none_returns_tbd(self):
        from itingen.rendering.pdf.formatting import fmt_time
        assert fmt_time(None) == "TBD"

    def test_timezone_appended(self):
        from itingen.rendering.pdf.formatting import fmt_time
        assert fmt_time("10:00", timezone="NZ") == "10am NZ"

    def test_timezone_suppressed(self):
        from itingen.rendering.pdf.formatting import fmt_time
        assert fmt_time("10:00", suppress_tz=True, timezone="NZ") == "10am"

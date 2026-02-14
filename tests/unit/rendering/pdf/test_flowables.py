"""Tests for custom ReportLab flowables — KindIconCircle, EventThumb, HeroBanner."""

import io
from pathlib import Path

import pytest
from PIL import Image as PILImage
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.pdfgen.canvas import Canvas

from itingen.rendering.pdf.flowables import (
    KindIconCircle,
    BannerImage,
    EventThumb,
    HeroBanner,
)
from itingen.rendering.pdf.themes import PDFTheme


@pytest.fixture
def theme():
    return PDFTheme()


@pytest.fixture
def canvas_buf():
    """Create a canvas writing to a BytesIO buffer for testing."""
    buf = io.BytesIO()
    c = Canvas(buf, pagesize=LETTER)
    return c, buf


@pytest.fixture
def sample_image(tmp_path):
    """Create a small test image and return its path."""
    path = tmp_path / "test.png"
    img = PILImage.new("RGB", (200, 200), color="blue")
    img.save(path)
    return str(path)


@pytest.fixture
def sample_jpeg(tmp_path):
    path = tmp_path / "test.jpg"
    img = PILImage.new("RGB", (200, 200), color="red")
    img.save(path, format="JPEG")
    return str(path)


class TestKindIconCircle:
    def test_wrap_returns_size(self, theme):
        icon = KindIconCircle(kind="meal", icon_name="restaurant", theme=theme, size=15)
        w, h = icon.wrap(100, 100)
        assert w == 15
        assert h == 15

    def test_draw_does_not_error(self, theme, canvas_buf):
        c, _ = canvas_buf
        icon = KindIconCircle(kind="meal", icon_name="restaurant", theme=theme)
        icon.drawOn(c, 0, 0)

    def test_fallback_glyph_for_unknown_icon(self, theme, canvas_buf):
        c, _ = canvas_buf
        icon = KindIconCircle(kind="drive", icon_name="nonexistent_icon", theme=theme)
        # Should not raise — falls back to letter
        icon.drawOn(c, 0, 0)


class TestBannerImage:
    def test_wrap_returns_dimensions(self):
        banner = BannerImage(path="/nonexistent", width=6.5 * inch, height=3 * inch)
        w, h = banner.wrap(100, 100)
        assert w == 6.5 * inch
        assert h == 3 * inch

    def test_draw_with_real_image(self, sample_image, canvas_buf):
        c, _ = canvas_buf
        banner = BannerImage(path=sample_image, width=6.5 * inch, height=3 * inch)
        banner.drawOn(c, 0, 0)

    def test_draw_with_nonexistent_path(self, canvas_buf):
        c, _ = canvas_buf
        banner = BannerImage(path="/nonexistent.jpg", width=100, height=100)
        # Should not raise
        banner.drawOn(c, 0, 0)


class TestEventThumb:
    def test_wrap_returns_size(self):
        thumb = EventThumb(path="/nonexistent", size=0.66 * inch)
        w, h = thumb.wrap(100, 100)
        assert w == 0.66 * inch
        assert h == 0.66 * inch

    def test_draw_png_converts_to_jpeg(self, sample_image, canvas_buf):
        c, _ = canvas_buf
        thumb = EventThumb(path=sample_image, size=0.66 * inch)
        thumb.drawOn(c, 0, 0)

    def test_draw_jpeg(self, sample_jpeg, canvas_buf):
        c, _ = canvas_buf
        thumb = EventThumb(path=sample_jpeg, size=0.66 * inch)
        thumb.drawOn(c, 0, 0)

    def test_draw_nonexistent_path(self, canvas_buf):
        c, _ = canvas_buf
        thumb = EventThumb(path="/nonexistent.png", size=0.66 * inch)
        # Should not raise
        thumb.drawOn(c, 0, 0)


class TestHeroBanner:
    def test_wrap_returns_dimensions(self, theme):
        hero = HeroBanner(
            banner_path="/nonexistent",
            width=7 * inch,
            height=4 * inch,
            header_flowables=[],
            weather_card=None,
            theme=theme,
        )
        w, h = hero.wrap(100, 100)
        assert w == 7 * inch
        assert h == 4 * inch

    def test_draw_with_image_and_no_weather(self, sample_image, canvas_buf, theme):
        c, _ = canvas_buf
        from reportlab.platypus import Paragraph
        from reportlab.lib.styles import getSampleStyleSheet

        styles = getSampleStyleSheet()
        header = [Paragraph("Test Title", styles["Title"])]

        hero = HeroBanner(
            banner_path=sample_image,
            width=7 * inch,
            height=4 * inch,
            header_flowables=header,
            weather_card=None,
            theme=theme,
        )
        hero.drawOn(c, 0, 0)

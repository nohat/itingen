"""Tests for PDF themes — verifies PDFTheme dataclass defaults."""

from itingen.rendering.pdf.themes import PDFTheme


def test_theme_default_colors():
    """Test that default color attributes are present."""
    theme = PDFTheme()
    assert theme.ink is not None
    assert theme.muted is not None
    assert theme.accent is not None


def test_theme_default_margins():
    """Test that default margin values are set."""
    theme = PDFTheme()
    assert theme.margin_left > 0
    assert theme.margin_right > 0

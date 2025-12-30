"""Tests for PDF themes and component-based rendering."""

import pytest
import yaml
from itingen.rendering.pdf.themes import PDFTheme

@pytest.fixture
def sample_theme_yaml(tmp_path):
    """Create a sample theme YAML file."""
    theme_data = {
        "pdf_theme": {
            "colors": {
                "primary": "#1976D2",
                "on_primary": "#FFFFFF",
                "background": "#FAFAFA"
            },
            "fonts": {
                "body": "helvetica",
                "heading": "helvetica"
            },
            "spacing": {
                "padding": 0.75
            }
        }
    }
    theme_file = tmp_path / "theme.yaml"
    with open(theme_file, "w") as f:
        yaml.dump(theme_data, f)
    return theme_file

def test_theme_loading_from_yaml(sample_theme_yaml):
    """Test that a theme can be loaded from a YAML file."""
    theme = PDFTheme.from_yaml(sample_theme_yaml)
    assert theme.colors["primary"] == "#1976D2"
    assert theme.fonts["body"] == "helvetica"
    assert theme.spacing["padding"] == 0.75

def test_theme_default_values():
    """Test that default values are used when not provided."""
    theme = PDFTheme()
    assert "primary" in theme.colors
    assert "body" in theme.fonts

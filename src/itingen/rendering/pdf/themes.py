"""PDF Theme management for the itinerary system.

AIDEV-NOTE: Manages colors, fonts, and spacing for PDF generation.
Supports loading from YAML configuration for trip-specific styling.
"""

from typing import Dict, Optional
from pathlib import Path
import yaml


class PDFTheme:
    """Configuration for PDF visual style."""

    DEFAULT_COLORS = {
        "primary": "#000000",
        "on_primary": "#FFFFFF",
        "background": "#FFFFFF",
        "surface": "#FFFFFF",
        "text": "#000000",
    }

    DEFAULT_FONTS = {
        "body": "helvetica",
        "heading": "helvetica",
    }

    DEFAULT_SPACING = {
        "padding": 0.5,
        "margin_top": 0.5,
        "margin_bottom": 0.5,
    }

    def __init__(
        self,
        colors: Optional[Dict[str, str]] = None,
        fonts: Optional[Dict[str, str]] = None,
        spacing: Optional[Dict[str, float]] = None,
    ):
        """Initialize theme with optional overrides.
        
        Args:
            colors: Dict of color overrides (hex strings)
            fonts: Dict of font name overrides
            spacing: Dict of spacing value overrides
        """
        self.colors = self.DEFAULT_COLORS.copy()
        if colors:
            self.colors.update(colors)

        self.fonts = self.DEFAULT_FONTS.copy()
        if fonts:
            self.fonts.update(fonts)

        self.spacing = self.DEFAULT_SPACING.copy()
        if spacing:
            self.spacing.update(spacing)

    @classmethod
    def from_yaml(cls, yaml_path: Path) -> "PDFTheme":
        """Load theme from a YAML file.
        
        Expects a structure like:
        pdf_theme:
            colors: ...
            fonts: ...
            spacing: ...
        """
        with open(yaml_path, "r") as f:
            config = yaml.safe_load(f)

        theme_config = config.get("pdf_theme", {})
        return cls(
            colors=theme_config.get("colors"),
            fonts=theme_config.get("fonts"),
            spacing=theme_config.get("spacing"),
        )

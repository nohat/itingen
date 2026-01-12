"""Font management for ReportLab PDF generation with Unicode support.

AIDEV-NOTE: Ported from scaffold POC. Downloads and caches fonts from GitHub,
registers them with ReportLab. Supports SourceSans3, NotoSans, DejaVuSans fallback chain.
"""

import os
from pathlib import Path
from typing import Optional, Tuple
import requests
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


def _get_cache_dir() -> Path:
    """Get or create the font cache directory."""
    cache_dir = Path.home() / ".cache" / "itingen" / "pdf_fonts"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def _download_to_path(url: str, path: Path) -> None:
    """Download a file from URL to path."""
    offline = os.environ.get("ITINGEN_OFFLINE", "").strip().lower() in {"1", "true", "yes", "on"}
    if offline:
        raise RuntimeError("offline mode enabled")
    
    resp = requests.get(
        url,
        timeout=30,
        headers={"User-Agent": "Mozilla/5.0 (itingen; +local script)"},
    )
    resp.raise_for_status()
    path.write_bytes(resp.content)


def _ensure_source_sans_3_cached() -> Tuple[Optional[Path], Optional[Path]]:
    """Download and cache SourceSans3 fonts if not present."""
    cache_dir = _get_cache_dir()
    reg_path = cache_dir / "SourceSans3-Regular.ttf"
    bold_path = cache_dir / "SourceSans3-Semibold.ttf"
    
    reg_url = "https://raw.githubusercontent.com/adobe-fonts/source-sans/release/TTF/SourceSans3-Regular.ttf"
    bold_url = "https://raw.githubusercontent.com/adobe-fonts/source-sans/release/TTF/SourceSans3-Semibold.ttf"
    
    try:
        if not reg_path.exists():
            _download_to_path(reg_url, reg_path)
        if not bold_path.exists():
            _download_to_path(bold_url, bold_path)
        return (reg_path, bold_path)
    except Exception:
        return (None, None)


def _ensure_noto_sans_cached() -> Tuple[Optional[Path], Optional[Path]]:
    """Download and cache NotoSans fonts if not present."""
    cache_dir = _get_cache_dir()
    reg_path = cache_dir / "NotoSans-Regular.ttf"
    bold_path = cache_dir / "NotoSans-Bold.ttf"
    
    reg_url = "https://raw.githubusercontent.com/googlefonts/noto-fonts/main/hinted/ttf/NotoSans/NotoSans-Regular.ttf"
    bold_url = "https://raw.githubusercontent.com/googlefonts/noto-fonts/main/hinted/ttf/NotoSans/NotoSans-Bold.ttf"
    
    try:
        if not reg_path.exists():
            _download_to_path(reg_url, reg_path)
        if not bold_path.exists():
            _download_to_path(bold_url, bold_path)
        return (reg_path, bold_path)
    except Exception:
        return (None, None)


def register_fonts() -> None:
    """Register Unicode-capable fonts with ReportLab.
    
    Tries to register fonts in order of preference:
    1. SourceSans3 (preferred UI font)
    2. NotoSans (fallback with good Unicode coverage)
    3. DejaVuSans (system font fallback if available)
    
    Falls back to Helvetica if none are available.
    """
    # Register SourceSans3
    if "SourceSans3" not in pdfmetrics.getRegisteredFontNames():
        reg_path, bold_path = _ensure_source_sans_3_cached()
        if reg_path and bold_path and reg_path.exists() and bold_path.exists():
            try:
                pdfmetrics.registerFont(TTFont("SourceSans3", str(reg_path)))
                pdfmetrics.registerFont(TTFont("SourceSans3-Semibold", str(bold_path)))
            except Exception:
                pass
    
    # Register NotoSans
    if "NotoSans" not in pdfmetrics.getRegisteredFontNames():
        reg_path, bold_path = _ensure_noto_sans_cached()
        if reg_path and bold_path and reg_path.exists() and bold_path.exists():
            try:
                pdfmetrics.registerFont(TTFont("NotoSans", str(reg_path)))
                pdfmetrics.registerFont(TTFont("NotoSans-Bold", str(bold_path)))
            except Exception:
                pass
    
    # Try to register DejaVuSans from system
    if "DejaVuSans" not in pdfmetrics.getRegisteredFontNames():
        try:
            pdfmetrics.registerFont(TTFont("DejaVuSans", "/Library/Fonts/DejaVuSans.ttf"))
            pdfmetrics.registerFont(TTFont("DejaVuSans-Bold", "/Library/Fonts/DejaVuSans-Bold.ttf"))
        except Exception:
            pass


def get_ui_font() -> str:
    """Get the best available UI font name."""
    if "SourceSans3" in pdfmetrics.getRegisteredFontNames():
        return "SourceSans3"
    elif "NotoSans" in pdfmetrics.getRegisteredFontNames():
        return "NotoSans"
    elif "DejaVuSans" in pdfmetrics.getRegisteredFontNames():
        return "DejaVuSans"
    else:
        return "Helvetica"


def get_ui_bold_font() -> str:
    """Get the best available UI bold font name."""
    if "SourceSans3-Semibold" in pdfmetrics.getRegisteredFontNames():
        return "SourceSans3-Semibold"
    elif "NotoSans-Bold" in pdfmetrics.getRegisteredFontNames():
        return "NotoSans-Bold"
    elif "DejaVuSans-Bold" in pdfmetrics.getRegisteredFontNames():
        return "DejaVuSans-Bold"
    else:
        return "Helvetica-Bold"

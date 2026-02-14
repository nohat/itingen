"""Font management for ReportLab PDF generation.

AIDEV-NOTE: Downloads and caches fonts from GitHub. Supports CormorantGaramond
(headlines), SourceSerif4 (body), SourceSans3 (UI), MaterialIcons (kind glyphs),
NotoSans + DejaVuSans fallback chain.
"""

import io
import os
import re
import zipfile
from pathlib import Path
from typing import Dict, Optional, Tuple

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
    offline = os.environ.get("ITINGEN_OFFLINE", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    if offline:
        raise RuntimeError("offline mode enabled")

    resp = requests.get(
        url,
        timeout=30,
        headers={"User-Agent": "Mozilla/5.0 (itingen; +local script)"},
    )
    resp.raise_for_status()
    path.write_bytes(resp.content)


# ---------------------------------------------------------------------------
# SourceSans3
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# NotoSans
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Cormorant Garamond (headline font — ZIP download from GitHub)
# ---------------------------------------------------------------------------

def _ensure_cormorant_garamond_cached() -> Tuple[Optional[Path], Optional[Path]]:
    """Download and cache Cormorant Garamond (Regular + SemiBold) from GitHub ZIP."""
    cache_dir = _get_cache_dir()
    reg_path = cache_dir / "CormorantGaramond-Regular.ttf"
    bold_path = cache_dir / "CormorantGaramond-SemiBold.ttf"

    try:
        offline = os.environ.get("ITINGEN_OFFLINE", "").strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
        if offline:
            return (None, None)

        if reg_path.exists() and bold_path.exists():
            return (reg_path, bold_path)

        url = "https://github.com/CatharsisFonts/Cormorant/releases/latest/download/Cormorant_Install.zip"
        resp = requests.get(
            url,
            timeout=60,
            headers={"User-Agent": "Mozilla/5.0 (itingen; +local script)"},
        )
        resp.raise_for_status()
        zf = zipfile.ZipFile(io.BytesIO(resp.content))
        names = zf.namelist()

        def _find_member(filename: str) -> str:
            for n in names:
                if n.lower().endswith("/" + filename.lower()) or n.lower().endswith(
                    filename.lower()
                ):
                    return n
            return ""

        reg_member = _find_member("CormorantGaramond-Regular.ttf")
        bold_member = _find_member("CormorantGaramond-SemiBold.ttf")
        if reg_member and not reg_path.exists():
            reg_path.write_bytes(zf.read(reg_member))
        if bold_member and not bold_path.exists():
            bold_path.write_bytes(zf.read(bold_member))

        if reg_path.exists() and bold_path.exists():
            return (reg_path, bold_path)
        return (None, None)
    except Exception:
        return (None, None)


# ---------------------------------------------------------------------------
# Source Serif 4 (body font)
# ---------------------------------------------------------------------------

def _ensure_source_serif_4_cached() -> Tuple[Optional[Path], Optional[Path]]:
    """Download and cache Source Serif 4 (Regular + Semibold)."""
    cache_dir = _get_cache_dir()
    reg_path = cache_dir / "SourceSerif4-Regular.ttf"
    bold_path = cache_dir / "SourceSerif4-Semibold.ttf"

    reg_url = "https://raw.githubusercontent.com/adobe-fonts/source-serif/release/TTF/SourceSerif4-Regular.ttf"
    bold_url = "https://raw.githubusercontent.com/adobe-fonts/source-serif/release/TTF/SourceSerif4-Semibold.ttf"

    try:
        offline = os.environ.get("ITINGEN_OFFLINE", "").strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
        if offline:
            return (None, None)

        if not reg_path.exists():
            _download_to_path(reg_url, reg_path)
        if not bold_path.exists():
            _download_to_path(bold_url, bold_path)
        return (reg_path, bold_path)
    except Exception:
        return (None, None)


# ---------------------------------------------------------------------------
# Material Icons (kind glyphs)
# ---------------------------------------------------------------------------

def _ensure_material_icons_cached() -> Tuple[Optional[Path], Optional[Path]]:
    """Download and cache Material Icons TTF + codepoints file."""
    cache_dir = _get_cache_dir()
    ttf_path = cache_dir / "MaterialIcons-Regular.ttf"
    codepoints_path = cache_dir / "MaterialIcons-Regular.codepoints"

    ttf_url = "https://raw.githubusercontent.com/google/material-design-icons/master/font/MaterialIcons-Regular.ttf"
    codepoints_url = "https://raw.githubusercontent.com/google/material-design-icons/master/font/MaterialIcons-Regular.codepoints"

    try:
        if not ttf_path.exists():
            _download_to_path(ttf_url, ttf_path)
        if not codepoints_path.exists():
            _download_to_path(codepoints_url, codepoints_path)
        return (ttf_path, codepoints_path)
    except Exception:
        return (None, None)


_CODEPOINTS_CACHE: Optional[Dict[str, int]] = None


def _load_material_codepoints() -> Dict[str, int]:
    """Parse Material Icons codepoints file → {name: unicode_int}."""
    global _CODEPOINTS_CACHE
    if isinstance(_CODEPOINTS_CACHE, dict):
        return _CODEPOINTS_CACHE

    _, codepoints_path = _ensure_material_icons_cached()
    mapping: Dict[str, int] = {}
    if codepoints_path and codepoints_path.exists():
        try:
            text = codepoints_path.read_text(encoding="utf-8")
            for line in text.splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = re.split(r"\s+", line)
                if len(parts) != 2:
                    continue
                name, hex_cp = parts
                try:
                    mapping[name.strip()] = int(hex_cp.strip(), 16)
                except Exception:
                    continue
        except Exception:
            mapping = {}

    _CODEPOINTS_CACHE = mapping
    return mapping


def _material_icon_char(icon_name: str) -> str:
    """Return the unicode character for a Material Icons glyph name."""
    cps = _load_material_codepoints()
    cp = cps.get(icon_name)
    if not isinstance(cp, int):
        return ""
    try:
        return chr(cp)
    except Exception:
        return ""


def _first_available_material_icon(*names: str) -> str:
    """Return the first icon name present in the MaterialIcons codepoints."""
    cps = _load_material_codepoints()
    for n in names:
        nn = (n or "").strip()
        if nn and nn in cps:
            return nn
    return ""


# ---------------------------------------------------------------------------
# Font registration
# ---------------------------------------------------------------------------

def register_fonts() -> None:
    """Register all font families with ReportLab.

    Registration order: CormorantGaramond, SourceSerif4, SourceSans3,
    MaterialIcons, NotoSans, DejaVuSans. Falls back to Helvetica.
    """
    # Cormorant Garamond (headline)
    if "CormorantGaramond" not in pdfmetrics.getRegisteredFontNames():
        reg_path, bold_path = _ensure_cormorant_garamond_cached()
        if reg_path and bold_path and reg_path.exists() and bold_path.exists():
            try:
                pdfmetrics.registerFont(TTFont("CormorantGaramond", str(reg_path)))
                pdfmetrics.registerFont(
                    TTFont("CormorantGaramond-Semibold", str(bold_path))
                )
            except Exception:
                pass

    # Source Serif 4 (body)
    if "SourceSerif4" not in pdfmetrics.getRegisteredFontNames():
        reg_path, bold_path = _ensure_source_serif_4_cached()
        if reg_path and bold_path and reg_path.exists() and bold_path.exists():
            try:
                pdfmetrics.registerFont(TTFont("SourceSerif4", str(reg_path)))
                pdfmetrics.registerFont(
                    TTFont("SourceSerif4-Semibold", str(bold_path))
                )
            except Exception:
                pass

    # SourceSans3 (UI)
    if "SourceSans3" not in pdfmetrics.getRegisteredFontNames():
        reg_path, bold_path = _ensure_source_sans_3_cached()
        if reg_path and bold_path and reg_path.exists() and bold_path.exists():
            try:
                pdfmetrics.registerFont(TTFont("SourceSans3", str(reg_path)))
                pdfmetrics.registerFont(
                    TTFont("SourceSans3-Semibold", str(bold_path))
                )
            except Exception:
                pass

    # Material Icons
    if "MaterialIcons" not in pdfmetrics.getRegisteredFontNames():
        ttf_path, _ = _ensure_material_icons_cached()
        if ttf_path and ttf_path.exists():
            try:
                pdfmetrics.registerFont(TTFont("MaterialIcons", str(ttf_path)))
            except Exception:
                pass

    # NotoSans (Unicode fallback)
    if "NotoSans" not in pdfmetrics.getRegisteredFontNames():
        reg_path, bold_path = _ensure_noto_sans_cached()
        if reg_path and bold_path and reg_path.exists() and bold_path.exists():
            try:
                pdfmetrics.registerFont(TTFont("NotoSans", str(reg_path)))
                pdfmetrics.registerFont(TTFont("NotoSans-Bold", str(bold_path)))
            except Exception:
                pass

    # DejaVuSans (system fallback)
    if "DejaVuSans" not in pdfmetrics.getRegisteredFontNames():
        try:
            pdfmetrics.registerFont(
                TTFont("DejaVuSans", "/Library/Fonts/DejaVuSans.ttf")
            )
            pdfmetrics.registerFont(
                TTFont("DejaVuSans-Bold", "/Library/Fonts/DejaVuSans-Bold.ttf")
            )
        except Exception:
            pass


def get_ui_font() -> str:
    """Get the best available UI font name (SourceSans3 preferred)."""
    for name in ("SourceSans3", "NotoSans", "DejaVuSans"):
        if name in pdfmetrics.getRegisteredFontNames():
            return name
    return "Helvetica"


def get_ui_bold_font() -> str:
    """Get the best available UI bold font name."""
    for name in ("SourceSans3-Semibold", "NotoSans-Bold", "DejaVuSans-Bold"):
        if name in pdfmetrics.getRegisteredFontNames():
            return name
    return "Helvetica-Bold"


def get_headline_font() -> str:
    """Get the headline font (CormorantGaramond-Semibold preferred)."""
    if "CormorantGaramond-Semibold" in pdfmetrics.getRegisteredFontNames():
        return "CormorantGaramond-Semibold"
    return get_ui_bold_font()


def get_body_font() -> str:
    """Get the body font (SourceSerif4 preferred)."""
    if "SourceSerif4" in pdfmetrics.getRegisteredFontNames():
        return "SourceSerif4"
    return get_ui_font()

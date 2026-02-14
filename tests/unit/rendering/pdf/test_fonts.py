"""Tests for PDF font management — Cormorant Garamond, Source Serif 4, Material Icons."""

import os
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from reportlab.pdfbase import pdfmetrics

from itingen.rendering.pdf.fonts import (
    _get_cache_dir,
    _ensure_cormorant_garamond_cached,
    _ensure_source_serif_4_cached,
    _ensure_material_icons_cached,
    _load_material_codepoints,
    _material_icon_char,
    register_fonts,
    get_ui_font,
    get_ui_bold_font,
    get_headline_font,
    get_body_font,
)


class TestCacheDir:
    def test_returns_path_under_home(self):
        cache_dir = _get_cache_dir()
        assert isinstance(cache_dir, Path)
        assert "itingen" in str(cache_dir)
        assert "pdf_fonts" in str(cache_dir)


class TestCormorantGaramondCaching:
    def test_returns_none_in_offline_mode(self, monkeypatch):
        monkeypatch.setenv("ITINGEN_OFFLINE", "1")
        reg, bold = _ensure_cormorant_garamond_cached()
        assert reg is None
        assert bold is None

    def test_returns_paths_when_cached(self, tmp_path, monkeypatch):
        monkeypatch.setattr("itingen.rendering.pdf.fonts._get_cache_dir", lambda: tmp_path)
        # Create fake cached files
        reg = tmp_path / "CormorantGaramond-Regular.ttf"
        bold = tmp_path / "CormorantGaramond-SemiBold.ttf"
        reg.write_bytes(b"fake font data")
        bold.write_bytes(b"fake font data")

        result_reg, result_bold = _ensure_cormorant_garamond_cached()
        assert result_reg == reg
        assert result_bold == bold


class TestSourceSerif4Caching:
    def test_returns_none_in_offline_mode(self, monkeypatch):
        monkeypatch.setenv("ITINGEN_OFFLINE", "1")
        reg, bold = _ensure_source_serif_4_cached()
        assert reg is None
        assert bold is None

    def test_returns_paths_when_cached(self, tmp_path, monkeypatch):
        monkeypatch.setattr("itingen.rendering.pdf.fonts._get_cache_dir", lambda: tmp_path)
        reg = tmp_path / "SourceSerif4-Regular.ttf"
        bold = tmp_path / "SourceSerif4-Semibold.ttf"
        reg.write_bytes(b"fake font data")
        bold.write_bytes(b"fake font data")

        result_reg, result_bold = _ensure_source_serif_4_cached()
        assert result_reg == reg
        assert result_bold == bold


class TestMaterialIconsCaching:
    def test_returns_none_in_offline_mode_uncached(self, tmp_path, monkeypatch):
        """Offline mode prevents download when files don't exist."""
        monkeypatch.setenv("ITINGEN_OFFLINE", "1")
        monkeypatch.setattr("itingen.rendering.pdf.fonts._get_cache_dir", lambda: tmp_path)
        ttf, codepoints = _ensure_material_icons_cached()
        assert ttf is None
        assert codepoints is None

    def test_returns_paths_when_cached(self, tmp_path, monkeypatch):
        monkeypatch.setattr("itingen.rendering.pdf.fonts._get_cache_dir", lambda: tmp_path)
        ttf = tmp_path / "MaterialIcons-Regular.ttf"
        codepoints = tmp_path / "MaterialIcons-Regular.codepoints"
        ttf.write_bytes(b"fake ttf data")
        codepoints.write_text("restaurant e56c\nhotel e53a\n")

        result_ttf, result_cp = _ensure_material_icons_cached()
        assert result_ttf == ttf
        assert result_cp == codepoints


class TestMaterialCodepoints:
    def test_loads_codepoints_from_file(self, tmp_path, monkeypatch):
        # Reset global cache
        import itingen.rendering.pdf.fonts as fonts_mod
        monkeypatch.setattr(fonts_mod, "_CODEPOINTS_CACHE", None)
        monkeypatch.setattr("itingen.rendering.pdf.fonts._get_cache_dir", lambda: tmp_path)

        codepoints_path = tmp_path / "MaterialIcons-Regular.codepoints"
        codepoints_path.write_text("restaurant e56c\nhotel e53a\ndirections_car e531\n")
        # Also need a fake TTF so _ensure_material_icons_cached succeeds
        ttf_path = tmp_path / "MaterialIcons-Regular.ttf"
        ttf_path.write_bytes(b"fake ttf")

        result = _load_material_codepoints()
        assert result["restaurant"] == 0xE56C
        assert result["hotel"] == 0xE53A
        assert result["directions_car"] == 0xE531

    def test_material_icon_char(self, tmp_path, monkeypatch):
        import itingen.rendering.pdf.fonts as fonts_mod
        monkeypatch.setattr(fonts_mod, "_CODEPOINTS_CACHE", {"restaurant": 0xE56C})

        char = _material_icon_char("restaurant")
        assert char == chr(0xE56C)

    def test_material_icon_char_unknown(self, monkeypatch):
        import itingen.rendering.pdf.fonts as fonts_mod
        monkeypatch.setattr(fonts_mod, "_CODEPOINTS_CACHE", {})

        char = _material_icon_char("nonexistent_icon")
        assert char == ""


class TestFontGetters:
    def test_get_headline_font_fallback(self):
        """When no Cormorant is registered, falls back to bold UI font."""
        result = get_headline_font()
        assert isinstance(result, str)
        assert len(result) > 0

    def test_get_body_font_fallback(self):
        """When no Source Serif is registered, falls back to UI font."""
        result = get_body_font()
        assert isinstance(result, str)
        assert len(result) > 0

    def test_get_ui_font_returns_string(self):
        result = get_ui_font()
        assert isinstance(result, str)

    def test_get_ui_bold_font_returns_string(self):
        result = get_ui_bold_font()
        assert isinstance(result, str)

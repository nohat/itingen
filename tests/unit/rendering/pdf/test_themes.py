"""Tests for PDF theme dataclass with kind colors and icon mappings."""

from reportlab.lib import colors

from itingen.rendering.pdf.themes import PDFTheme, KIND_COLORS, KIND_ICONS


class TestPDFTheme:
    def test_default_colors(self):
        theme = PDFTheme()
        assert theme.ink == colors.HexColor("#111827")
        assert theme.muted == colors.HexColor("#6B7280")
        assert theme.accent == colors.HexColor("#0F766E")

    def test_page_margins(self):
        theme = PDFTheme()
        assert theme.margin_left > 0
        assert theme.margin_right > 0
        assert theme.margin_top > 0
        assert theme.margin_bottom > 0

    def test_is_frozen_dataclass(self):
        theme = PDFTheme()
        # Should be immutable
        import pytest
        with pytest.raises(AttributeError):
            theme.ink = colors.black  # type: ignore


class TestKindColors:
    def test_meal_is_amber(self):
        assert KIND_COLORS["meal"] == colors.HexColor("#B45309")

    def test_activity_is_green(self):
        assert KIND_COLORS["activity"] == colors.HexColor("#16A34A")

    def test_lodging_is_violet(self):
        assert KIND_COLORS["lodging_checkin"] == colors.HexColor("#7C3AED")
        assert KIND_COLORS["lodging_stay"] == colors.HexColor("#7C3AED")
        assert KIND_COLORS["lodging_checkout"] == colors.HexColor("#7C3AED")

    def test_drive_is_gray(self):
        assert KIND_COLORS["drive"] == colors.HexColor("#4B5563")

    def test_ferry_is_blue(self):
        assert KIND_COLORS["ferry"] == colors.HexColor("#2563EB")

    def test_decision_is_orange(self):
        assert KIND_COLORS["decision"] == colors.HexColor("#C2410C")

    def test_unknown_kind_returns_muted(self):
        theme = PDFTheme()
        # Unknown kinds should get theme.muted via kind_icon_color()
        from itingen.rendering.pdf.themes import kind_icon_color
        result = kind_icon_color("totally_unknown_kind", theme)
        assert result == theme.muted


class TestKindIcons:
    def test_meal_icon(self):
        assert KIND_ICONS["meal"] == "restaurant"

    def test_flight_icons(self):
        assert KIND_ICONS["flight_departure"] == "flight_takeoff"
        assert KIND_ICONS["flight_arrival"] == "flight_land"

    def test_drive_icon(self):
        assert KIND_ICONS["drive"] == "directions_car"

    def test_walk_icon(self):
        assert KIND_ICONS["walk"] == "hiking"

    def test_unknown_kind_returns_empty(self):
        from itingen.rendering.pdf.themes import icon_name_for_kind
        result = icon_name_for_kind("totally_unknown_kind")
        assert result == ""

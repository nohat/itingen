"""PDF Theme — dataclass with scaffold-equivalent colors, kind mappings.

AIDEV-NOTE: Frozen dataclass replaces old dict-based PDFTheme. Colors use
Tailwind CSS palette names (ink=slate-900, muted=gray-500, etc.). Kind color
and icon mappings live here so flowables/components can look them up.
"""

from dataclasses import dataclass
from typing import Dict

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch


@dataclass(frozen=True)
class PDFTheme:
    """Visual styling configuration for PDF generation."""

    page_size: tuple = LETTER
    margin_left: float = 0.75 * inch
    margin_right: float = 0.75 * inch
    margin_top: float = 0.72 * inch
    margin_bottom: float = 0.70 * inch

    # Colors — Tailwind CSS palette
    ink: colors.Color = colors.HexColor("#111827")  # slate-900
    muted: colors.Color = colors.HexColor("#6B7280")  # gray-500
    line: colors.Color = colors.HexColor("#E5E7EB")  # gray-200
    accent: colors.Color = colors.HexColor("#0F766E")  # teal-700
    accent_soft: colors.Color = colors.HexColor("#CCFBF1")  # teal-100
    warn: colors.Color = colors.HexColor("#B45309")  # amber-700
    warn_soft: colors.Color = colors.HexColor("#FEF3C7")  # amber-100


# ---------------------------------------------------------------------------
# Kind → icon name mapping
# ---------------------------------------------------------------------------

KIND_ICONS: Dict[str, str] = {
    "meal": "restaurant",
    "drive": "directions_car",
    "activity": "local_activity",
    "lodging_checkin": "hotel",
    "flight_departure": "flight_takeoff",
    "flight_arrival": "flight_land",
    "transfer": "directions_car",
    "airport_buffer": "schedule",
    "lodging_stay": "hotel",
    "lodging_checkout": "hotel",
    "car_rental": "car_rental",
    "meet": "groups",
    "layover_buffer": "schedule",
    "ferry": "directions_boat",
    "coach": "directions_bus",
    "car_rental_pickup": "car_rental",
    "arrivals_buffer": "schedule",
    "activity_overnight": "nights_stay",
    "walk": "hiking",
    "sleep": "bedtime",
    "decision": "help_outline",
    "activity_return": "keyboard_return",
    "activity_checkin": "how_to_reg",
    "flight_boarding": "event_seat",
    "logistics": "settings",
}


def icon_name_for_kind(kind: str) -> str:
    """Return the Material Icon name for an event kind, or '' if unknown."""
    return KIND_ICONS.get(kind, "")


# ---------------------------------------------------------------------------
# Kind → color mapping
# ---------------------------------------------------------------------------

KIND_COLORS: Dict[str, colors.Color] = {
    "meal": colors.HexColor("#B45309"),  # amber-700
    "drive": colors.HexColor("#4B5563"),  # gray-600
    "activity": colors.HexColor("#16A34A"),  # green-600
    "lodging_checkin": colors.HexColor("#7C3AED"),  # violet-600
    "lodging_stay": colors.HexColor("#7C3AED"),  # violet-600
    "lodging_checkout": colors.HexColor("#7C3AED"),  # violet-600
    "transfer": colors.HexColor("#4B5563"),  # gray-600
    "car_rental": colors.HexColor("#4B5563"),  # gray-600
    "car_rental_pickup": colors.HexColor("#4B5563"),  # gray-600
    "meet": colors.HexColor("#4F46E5"),  # indigo-600
    "ferry": colors.HexColor("#2563EB"),  # blue-600
    "coach": colors.HexColor("#4B5563"),  # gray-600
    "walk": colors.HexColor("#16A34A"),  # green-600
    "decision": colors.HexColor("#C2410C"),  # orange-700
    "activity_return": colors.HexColor("#16A34A"),  # green-600
    "activity_checkin": colors.HexColor("#16A34A"),  # green-600
    "logistics": colors.HexColor("#4B5563"),  # gray-600
}

# These kinds use theme colors (accent/muted) rather than fixed colors,
# so they're resolved at runtime via kind_icon_color().
_THEME_ACCENT_KINDS = {"flight_departure", "flight_arrival", "flight_boarding"}
_THEME_MUTED_KINDS = {
    "airport_buffer",
    "layover_buffer",
    "arrivals_buffer",
    "activity_overnight",
    "sleep",
}


def kind_icon_color(kind: str, theme: PDFTheme) -> colors.Color:
    """Return the icon circle color for an event kind."""
    if kind in KIND_COLORS:
        return KIND_COLORS[kind]
    if kind in _THEME_ACCENT_KINDS:
        return theme.accent
    if kind in _THEME_MUTED_KINDS:
        return theme.muted
    return theme.muted

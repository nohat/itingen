"""PDF rendering components — scaffold-equivalent event row + day layout.

AIDEV-NOTE: EventComponent uses 2-row table: [time|heading|kind_badge] /
[thumb|body|""].  DayComponent uses HeroBanner with header overlays when
banner image is available, falls back to side-by-side header+weather.
"""

import os
from pathlib import Path
from typing import Any, Dict, List

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (
    KeepTogether,
    PageBreak,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from xml.sax.saxutils import escape

from itingen.core.domain.events import Event
from itingen.rendering.pdf.flowables import EventThumb, HeroBanner, KindIconCircle
from itingen.rendering.pdf.formatting import fmt_time
from itingen.rendering.pdf.themes import PDFTheme, icon_name_for_kind
from itingen.rendering.timeline import TimelineDay


class PDFComponent:
    """Base class for PDF layout components."""

    def render(self, story: List[Any], styles: Dict[str, ParagraphStyle], theme: PDFTheme, data: Any):
        raise NotImplementedError


class EventComponent(PDFComponent):
    """Renders a single event as a 2-row table with kind badge."""

    def render(
        self,
        story: List[Any],
        styles: Dict[str, ParagraphStyle],
        theme: PDFTheme,
        event: Event,
        *,
        suppress_tz: bool = False,
    ):
        heading = (event.event_heading or event.description or "Event").strip()
        kind = (event.kind or "").strip()

        t = fmt_time(
            event.time_local,
            suppress_tz=suppress_tz,
            timezone=getattr(event, "timezone", None),
        )

        # Build body content
        narrative = (getattr(event, "narrative", None) or "").strip()

        if narrative:
            body = escape(narrative)
            body_style = styles["body"]
        else:
            notes_bits: List[str] = []
            location = (event.location or "").strip()
            if location:
                notes_bits.append(f"<b>Location:</b> {escape(location)}")

            # Travel info
            travel_bits: List[str] = []
            travel_mode = getattr(event, "travel_mode", None)
            if travel_mode:
                travel_bits.append(str(travel_mode))
            if event.travel_from or event.travel_to:
                travel_bits.append(
                    f"{event.travel_from or ''} → {event.travel_to or ''}"
                )
            duration = getattr(event, "duration", None) or getattr(
                event, "duration_text", None
            )
            if duration:
                travel_bits.append(str(duration))
            travel_line = " | ".join([b for b in travel_bits if b.strip()])
            if travel_line:
                notes_bits.append(f"<b>Travel:</b> {escape(travel_line)}")

            if getattr(event, "hard_stop", None) is True:
                notes_bits.append("<b>Timing:</b> hard stop")
            if getattr(event, "coordination_point", None) is True:
                notes_bits.append("<b>Coordination:</b> regroup point")
            notes_val = getattr(event, "notes", None)
            if notes_val:
                notes_bits.append(
                    f"<b>Notes:</b> {escape(str(notes_val).strip())}"
                )

            body = "<br/>".join(notes_bits)
            body_style = styles["event_details"]

        # Kind badge
        kind_label = kind.replace("_", " ").strip() or "(type)"
        icon_name = icon_name_for_kind(kind)

        pill_bg = (
            theme.warn_soft
            if getattr(event, "hard_stop", None) is True
            else colors.whitesmoke
        )

        kind_badge = Table(
            [
                [
                    KindIconCircle(
                        kind=kind, icon_name=icon_name, theme=theme, size=12.5
                    ),
                    Paragraph(kind_label, styles["pill"]),
                ]
            ],
            colWidths=[0.22 * inch, 0.78 * inch],
            style=TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("ALIGN", (0, 0), (0, 0), "CENTER"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 4),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                    ("TOPPADDING", (0, 0), (-1, -1), 2),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                    ("BACKGROUND", (0, 0), (-1, -1), pill_bg),
                    ("BOX", (0, 0), (-1, -1), 1, theme.line),
                ]
            ),
        )

        # Thumbnail
        thumb_size = 0.66 * inch
        thumb_path = str(getattr(event, "image_path", "") or "").strip()
        thumb_cell: Any = ""
        if thumb_path and os.path.exists(thumb_path):
            thumb_cell = EventThumb(path=thumb_path, size=thumb_size)

        # 2-row table
        table = Table(
            [
                [
                    Paragraph(escape(t), styles["event_time"]),
                    Paragraph(escape(heading), styles["event_title"]),
                    kind_badge,
                ],
                [
                    thumb_cell,
                    Paragraph(body, body_style),
                    "",
                ],
            ],
            colWidths=[0.8 * inch, 5.2 * inch, 1.0 * inch],
            style=TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LINEBELOW", (0, 0), (-1, 0), 1, theme.line),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("ALIGN", (2, 0), (2, 0), "CENTER"),
                    ("ALIGN", (0, 1), (0, 1), "LEFT"),
                    ("VALIGN", (0, 1), (0, 1), "TOP"),
                    ("LEFTPADDING", (0, 1), (0, 1), 2),
                    ("RIGHTPADDING", (0, 1), (0, 1), 2),
                    ("TOPPADDING", (0, 1), (0, 1), 2),
                    ("BOTTOMPADDING", (0, 1), (0, 1), 4),
                ]
            ),
        )

        story.append(KeepTogether([table, Spacer(1, 10)]))


class DayComponent(PDFComponent):
    """Renders a full day with hero banner (or header+weather) and events."""

    def __init__(self):
        self.event_component = EventComponent()

    def render(
        self,
        story: List[Any],
        styles: Dict[str, ParagraphStyle],
        theme: PDFTheme,
        day: TimelineDay,
    ):
        story.append(PageBreak())

        # Build header flowables
        header_block: List[Any] = [
            Paragraph(escape(day.day_header), styles["title"]),
        ]

        # Check banner
        banner_path = day.banner_image_path
        has_banner = bool(banner_path and Path(banner_path).exists())

        # Build weather card (simple for now — full weather card comes later)
        weather_card = self._build_weather_card(styles, theme, day)

        if has_banner:
            # Compute banner height from image aspect ratio
            banner_h = self._compute_banner_height(banner_path, page_width=7.0 * inch)

            story.append(
                HeroBanner(
                    banner_path=banner_path,
                    width=7.0 * inch,
                    height=banner_h,
                    header_flowables=header_block,
                    weather_card=weather_card,
                    theme=theme,
                )
            )
            story.append(Spacer(1, 8))
        else:
            # No banner — header + weather side by side
            if weather_card:
                weather_w = 1.5 * inch
                header_w = 7.0 * inch - weather_w - 12
                cells = [[header_block, weather_card]]
                header_table = Table(
                    cells,
                    colWidths=[header_w, weather_w],
                    style=TableStyle(
                        [
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                            ("LEFTPADDING", (0, 0), (-1, -1), 0),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                            ("TOPPADDING", (0, 0), (-1, -1), 0),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                        ]
                    ),
                )
                story.append(header_table)
            else:
                for fl in header_block:
                    story.append(fl)
            story.append(Spacer(1, 12))

        # Wake-up info
        if day.wake_up_location:
            story.append(
                Paragraph(
                    f"<b>Wake up:</b> {escape(day.wake_up_location)}",
                    styles["meta"],
                )
            )

        if day.first_event_target_time and day.first_event_title:
            story.append(
                Paragraph(
                    f"<i>(Be ready by {escape(day.first_event_target_time)} "
                    f"for {escape(day.first_event_title)})</i>",
                    styles["muted"],
                )
            )

        story.append(Spacer(1, 0.15 * inch))

        # Determine timezone suppression
        day_tzs = {
            getattr(ev, "timezone", None)
            for ev in day.events
            if getattr(ev, "timezone", None)
        }
        suppress_tz = len(day_tzs) <= 1

        # Events
        for event in day.events:
            self.event_component.render(
                story, styles, theme, event, suppress_tz=suppress_tz
            )

        # Sleep info
        if day.sleep_location:
            story.append(Spacer(1, 0.15 * inch))
            story.append(
                Paragraph(
                    f"<b>Sleep at:</b> {escape(day.sleep_location)}",
                    styles["meta"],
                )
            )

    def _compute_banner_height(
        self, banner_path: str, page_width: float
    ) -> float:
        """Compute banner height from image aspect ratio, clamped."""
        try:
            ir = ImageReader(banner_path)
            iw, ih = ir.getSize()
            if iw > 0 and ih > 0:
                h = page_width * (float(ih) / float(iw))
            else:
                h = page_width * 9.0 / 16.0
        except Exception:
            h = page_width * 9.0 / 16.0

        h = max(2.0 * inch, h)
        h = min(6.25 * inch, h)
        return h

    def _build_weather_card(
        self,
        styles: Dict[str, ParagraphStyle],
        theme: PDFTheme,
        day: TimelineDay,
    ) -> Any:
        """Build a simple weather summary table, or None."""
        if day.weather_high is None and day.weather_low is None:
            return None

        weather_text = ""
        if day.weather_high is not None and day.weather_low is not None:
            weather_text = f"<b>{int(day.weather_low)}°F – {int(day.weather_high)}°F</b>"
        elif day.weather_high is not None:
            weather_text = f"<b>High: {int(day.weather_high)}°F</b>"
        elif day.weather_low is not None:
            weather_text = f"<b>Low: {int(day.weather_low)}°F</b>"

        if day.weather_conditions:
            weather_text += f"<br/>{escape(day.weather_conditions)}"

        weather_para = Paragraph(weather_text, styles["event_details"])
        return Table(
            [[weather_para]],
            style=TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("ALIGN", (0, 0), (0, 0), "RIGHT"),
                    ("BACKGROUND", (0, 0), (0, 0), colors.HexColor("#F3F4F6")),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            ),
        )

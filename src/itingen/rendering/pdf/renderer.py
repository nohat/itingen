"""PDF renderer — scaffold-equivalent typographic scale + header/footer.

AIDEV-NOTE: Uses ReportLab (not FPDF2) with Unicode font support.
Typography scale: 11 styles across 3 font families (CormorantGaramond headlines,
SourceSerif4 body, SourceSans3 UI). Header/footer via onPage callback.
"""

from typing import Any, Dict, List, Optional, Protocol

from reportlab.lib.enums import TA_LEFT, TA_RIGHT
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    PageTemplate,
    Paragraph,
    Spacer,
)

from itingen.core.base import BaseEmitter
from itingen.core.domain.events import Event
from itingen.rendering.pdf.fonts import (
    get_body_font,
    get_headline_font,
    get_ui_bold_font,
    get_ui_font,
    register_fonts,
)
from itingen.rendering.pdf.formatting import fmt_time  # noqa: F401 (re-export)
from itingen.rendering.pdf.themes import PDFTheme
from itingen.rendering.timeline import TimelineDay, TimelineProcessor


class _Pdf14Canvas(Canvas):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("pdfVersion", (1, 4))
        super().__init__(*args, **kwargs)


class BannerGenerator(Protocol):
    def generate(self, days: List[TimelineDay]) -> List[TimelineDay]: ...


def build_styles(theme: PDFTheme) -> Dict[str, ParagraphStyle]:
    """Build the 11-style typography scale matching scaffold output."""
    styles = getSampleStyleSheet()

    ui_font = get_ui_font()
    ui_bold = get_ui_bold_font()
    body_font = get_body_font()
    headline_font = get_headline_font()

    return {
        "eyebrow": ParagraphStyle(
            "eyebrow",
            parent=styles["Normal"],
            fontName=ui_bold,
            fontSize=8.5,
            leading=10.5,
            textColor=theme.muted,
            spaceAfter=1,
            alignment=TA_LEFT,
        ),
        "topline": ParagraphStyle(
            "topline",
            parent=styles["Normal"],
            fontName=ui_bold,
            fontSize=10,
            leading=12.5,
            textColor=theme.ink,
            spaceAfter=2,
            alignment=TA_LEFT,
        ),
        "title": ParagraphStyle(
            "title",
            parent=styles["Title"],
            fontName=headline_font,
            fontSize=21,
            leading=23,
            textColor=theme.ink,
            spaceAfter=2,
            alignment=TA_LEFT,
        ),
        "subtitle": ParagraphStyle(
            "subtitle",
            parent=styles["Normal"],
            fontName=ui_font,
            fontSize=9.5,
            leading=12.5,
            textColor=theme.muted,
            spaceAfter=10,
            alignment=TA_LEFT,
        ),
        "subhead": ParagraphStyle(
            "subhead",
            parent=styles["Normal"],
            fontName=ui_font,
            fontSize=9.5,
            leading=12.8,
            textColor=theme.muted,
            spaceAfter=0,
            alignment=TA_LEFT,
        ),
        "body": ParagraphStyle(
            "body",
            parent=styles["Normal"],
            fontName=body_font,
            fontSize=10,
            leading=14,
            textColor=theme.ink,
            alignment=TA_LEFT,
        ),
        "overview_body": ParagraphStyle(
            "overview_body",
            parent=styles["Normal"],
            fontName=body_font,
            fontSize=10,
            leading=15.2,
            textColor=theme.ink,
            alignment=TA_LEFT,
        ),
        "event_title": ParagraphStyle(
            "event_title",
            parent=styles["Normal"],
            fontName=ui_bold,
            fontSize=10.8,
            leading=13.5,
            textColor=theme.ink,
            alignment=TA_LEFT,
        ),
        "event_time": ParagraphStyle(
            "event_time",
            parent=styles["Normal"],
            fontName=ui_font,
            fontSize=8.7,
            leading=11,
            textColor=theme.muted,
            alignment=TA_LEFT,
        ),
        "event_details": ParagraphStyle(
            "event_details",
            parent=styles["Normal"],
            fontName=ui_font,
            fontSize=9.2,
            leading=12.5,
            textColor=theme.muted,
            alignment=TA_LEFT,
        ),
        "pill": ParagraphStyle(
            "pill",
            parent=styles["Normal"],
            fontName=ui_bold,
            fontSize=8.5,
            leading=10,
            textColor=theme.ink,
            alignment=TA_LEFT,
        ),
        "meta": ParagraphStyle(
            "meta",
            parent=styles["Normal"],
            fontName=ui_font,
            fontSize=9,
            leading=12,
            textColor=theme.muted,
            spaceAfter=6,
            alignment=TA_LEFT,
        ),
        "muted": ParagraphStyle(
            "muted",
            parent=styles["Normal"],
            fontName=ui_font,
            fontSize=9,
            leading=12,
            textColor=theme.muted,
            alignment=TA_LEFT,
        ),
        "material_icon": ParagraphStyle(
            "material_icon",
            parent=styles["Normal"],
            fontName=(
                "MaterialIcons"
                if "MaterialIcons" in pdfmetrics.getRegisteredFontNames()
                else ui_bold
            ),
            fontSize=11,
            leading=12,
            textColor=theme.muted,
            alignment=TA_LEFT,
        ),
        "tiny": ParagraphStyle(
            "tiny",
            parent=styles["Normal"],
            fontName=ui_font,
            fontSize=7,
            leading=9,
            textColor=theme.muted,
            alignment=TA_LEFT,
        ),
        "tiny_right": ParagraphStyle(
            "tiny_right",
            parent=styles["Normal"],
            fontName=ui_font,
            fontSize=7,
            leading=9,
            textColor=theme.muted,
            alignment=TA_RIGHT,
        ),
    }


def draw_header_footer(canvas, doc, *, theme: PDFTheme) -> None:
    """Draw page footer with rule and page number."""
    canvas.saveState()
    canvas.setFillColor(theme.muted)
    canvas.setFont("Helvetica", 8)

    # Footer rule
    canvas.line(
        theme.margin_left,
        theme.margin_bottom - 0.20 * inch,
        doc.pagesize[0] - theme.margin_right,
        theme.margin_bottom - 0.20 * inch,
    )

    # Page number
    canvas.drawRightString(
        doc.pagesize[0] - theme.margin_right,
        theme.margin_bottom - 0.35 * inch,
        f"Page {doc.page}",
    )
    canvas.restoreState()


class PDFEmitter(BaseEmitter[Event]):
    """Emitter that generates a PDF representation of the itinerary.

    AIDEV-NOTE: Uses ReportLab (not FPDF2) with Unicode font support.
    Supports daily aggregation, banners, and thumbnails via TimelineProcessor.
    """

    def __init__(
        self,
        theme: Optional[PDFTheme] = None,
        banner_generator: Optional[BannerGenerator] = None,
    ):
        from itingen.rendering.pdf.components import DayComponent

        self.theme = theme or PDFTheme()
        self.day_component = DayComponent()
        self.timeline_processor = TimelineProcessor()
        self.banner_generator = banner_generator

        register_fonts()

    def emit(self, itinerary: List[Event], output_path: str) -> str:
        """Write the itinerary to a PDF file using ReportLab."""
        from pathlib import Path

        path = Path(output_path)
        if not path.suffix:
            path = path.with_suffix(".pdf")
        path.parent.mkdir(parents=True, exist_ok=True)

        timeline_days = self.timeline_processor.process(itinerary)

        if self.banner_generator is not None:
            timeline_days = self.banner_generator.generate(timeline_days)

        theme = self.theme

        doc = BaseDocTemplate(
            str(path),
            pagesize=theme.page_size,
            leftMargin=theme.margin_left,
            rightMargin=theme.margin_right,
            topMargin=theme.margin_top,
            bottomMargin=theme.margin_bottom,
            title="Trip Itinerary",
        )

        frame = Frame(
            doc.leftMargin,
            doc.bottomMargin,
            doc.width,
            doc.height,
            id="normal",
        )

        def _on_page(canvas, doc_obj):
            draw_header_footer(canvas, doc_obj, theme=theme)

        doc.addPageTemplates(
            [PageTemplate(id="main", frames=[frame], onPage=_on_page)]
        )

        styles = build_styles(theme)

        story: List[Any] = []

        # Title page
        story.append(Spacer(1, 2 * inch))
        story.append(Paragraph("Trip Itinerary", styles["title"]))
        story.append(Spacer(1, 0.3 * inch))

        if timeline_days:
            start_date = timeline_days[0].date_str
            end_date = timeline_days[-1].date_str
            story.append(
                Paragraph(f"{start_date} to {end_date}", styles["subtitle"])
            )

        for day in timeline_days:
            self.day_component.render(story, styles, theme, day)

        doc.build(story, canvasmaker=_Pdf14Canvas)
        return str(path)

from typing import List, Optional, Protocol
from pathlib import Path
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib import colors
from itingen.core.base import BaseEmitter
from itingen.core.domain.events import Event
from itingen.rendering.pdf.themes import PDFTheme
from itingen.rendering.pdf.components import DayComponent
from itingen.rendering.pdf.fonts import register_fonts, get_ui_font, get_ui_bold_font
from itingen.rendering.timeline import TimelineProcessor, TimelineDay


class BannerGenerator(Protocol):
    def generate(self, days: List[TimelineDay]) -> List[TimelineDay]: ...

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
        self.theme = theme or PDFTheme()
        self.day_component = DayComponent()
        self.timeline_processor = TimelineProcessor()
        self.banner_generator = banner_generator
        
        # Register Unicode fonts on initialization
        register_fonts()

    def emit(self, itinerary: List[Event], output_path: str) -> str:
        """Write the itinerary to a PDF file using ReportLab."""
        path = Path(output_path)
        if not path.suffix:
            path = path.with_suffix(".pdf")
        
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Process events into timeline days
        timeline_days = self.timeline_processor.process(itinerary)

        if self.banner_generator is not None:
            timeline_days = self.banner_generator.generate(timeline_days)
        
        # Create ReportLab document
        doc = BaseDocTemplate(
            str(path),
            pagesize=LETTER,
            leftMargin=0.75 * inch,
            rightMargin=0.75 * inch,
            topMargin=0.72 * inch,
            bottomMargin=0.70 * inch,
            title="Trip Itinerary",
        )
        
        frame = Frame(
            doc.leftMargin,
            doc.bottomMargin,
            doc.width,
            doc.height,
            id="normal",
        )
        
        doc.addPageTemplates([PageTemplate(id="main", frames=[frame])])
        
        # Build styles
        styles = self._build_styles()
        
        # Build story (content)
        story = []
        
        # Title page
        story.append(Spacer(1, 2 * inch))
        story.append(Paragraph("Trip Itinerary", styles["itinerary_title"]))
        story.append(Spacer(1, 0.3 * inch))
        
        if timeline_days:
            start_date = timeline_days[0].date_str
            end_date = timeline_days[-1].date_str
            story.append(Paragraph(f"{start_date} to {end_date}", styles["itinerary_subtitle"]))
        
        # Render each day
        for day in timeline_days:
            self.day_component.render(story, styles, self.theme, day)
        
        doc.build(story)
        return str(path)

    def _build_styles(self):
        """Build ReportLab paragraph styles with Unicode fonts."""
        styles = getSampleStyleSheet()
        
        ui_font = get_ui_font()
        ui_bold = get_ui_bold_font()
        
        # Create custom styles with unique names
        styles.add(ParagraphStyle(
            name="itinerary_title",
            parent=styles["Heading1"],
            fontName=ui_bold,
            fontSize=24,
            leading=28,
            textColor=colors.HexColor(self.theme.colors.get("primary", "#0F766E")),
            alignment=TA_CENTER,
            spaceAfter=12,
        ))
        
        styles.add(ParagraphStyle(
            name="itinerary_subtitle",
            parent=styles["Normal"],
            fontName=ui_font,
            fontSize=14,
            leading=18,
            textColor=colors.HexColor(self.theme.colors.get("text", "#111827")),
            alignment=TA_CENTER,
            spaceAfter=20,
        ))
        
        styles.add(ParagraphStyle(
            name="day_header",
            parent=styles["Heading2"],
            fontName=ui_bold,
            fontSize=18,
            leading=22,
            textColor=colors.HexColor(self.theme.colors.get("primary", "#0F766E")),
            alignment=TA_LEFT,
            spaceAfter=10,
        ))
        
        styles.add(ParagraphStyle(
            name="itinerary_body",
            parent=styles["Normal"],
            fontName=ui_font,
            fontSize=10,
            leading=14,
            textColor=colors.HexColor(self.theme.colors.get("text", "#111827")),
            alignment=TA_LEFT,
        ))
        
        styles.add(ParagraphStyle(
            name="event_heading",
            parent=styles["Normal"],
            fontName=ui_bold,
            fontSize=12,
            leading=15,
            textColor=colors.HexColor(self.theme.colors.get("text", "#111827")),
            alignment=TA_LEFT,
        ))
        
        styles.add(ParagraphStyle(
            name="event_details",
            parent=styles["Normal"],
            fontName=ui_font,
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#6B7280"),
            alignment=TA_LEFT,
        ))
        
        return styles

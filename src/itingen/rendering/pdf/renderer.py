from typing import List, Optional, Tuple, Protocol
from pathlib import Path
from fpdf import FPDF
from itingen.core.base import BaseEmitter
from itingen.core.domain.events import Event
from itingen.rendering.pdf.themes import PDFTheme
from itingen.rendering.pdf.components import DayComponent
from itingen.rendering.timeline import TimelineProcessor, TimelineDay


class BannerGenerator(Protocol):
    def generate(self, days: List[TimelineDay]) -> List[TimelineDay]: ...

class PDFEmitter(BaseEmitter[Event]):
    """Emitter that generates a PDF representation of the itinerary.
    
    AIDEV-NOTE: Uses a theme and components for flexible styling.
    Now supports daily aggregation, banners, and thumbnails via TimelineProcessor.
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

    def emit(self, itinerary: List[Event], output_path: str) -> str:
        """Write the itinerary to a PDF file."""
        path = Path(output_path)
        if not path.suffix:
            path = path.with_suffix(".pdf")
        
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Process events into timeline days
        timeline_days = self.timeline_processor.process(itinerary)

        if self.banner_generator is not None:
            timeline_days = self.banner_generator.generate(timeline_days)
        
        # Initialize PDF
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # Render title page
        pdf.add_page()
        pdf.set_font(self.theme.fonts["heading"], "B", 24)
        pdf.set_text_color(*self._hex_to_rgb(self.theme.colors["primary"]))
        
        # Title vertical centering
        pdf.set_y(pdf.h / 3)
        pdf.cell(0, 10, "Trip Itinerary", ln=True, align="C")
        
        # Date range
        if timeline_days:
            start_date = timeline_days[0].date_str
            end_date = timeline_days[-1].date_str
            pdf.set_font(self.theme.fonts["body"], "", 14)
            pdf.set_text_color(*self._hex_to_rgb(self.theme.colors["text"]))
            pdf.ln(5)
            pdf.cell(0, 10, f"{start_date} to {end_date}", ln=True, align="C")

        # Render each day
        for day in timeline_days:
            self.day_component.render(pdf, self.theme, day)
        
        pdf.output(str(path))
        return str(path)

    def _hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """Convert hex color string to RGB tuple."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

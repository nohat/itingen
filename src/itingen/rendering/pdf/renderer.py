from typing import List, Optional
from pathlib import Path
from fpdf import FPDF
from fpdf.enums import XPos, YPos
from itingen.core.base import BaseEmitter
from itingen.core.domain.events import Event
from itingen.rendering.pdf.themes import PDFTheme
from itingen.rendering.pdf.components import EventComponent

class PDFEmitter(BaseEmitter[Event]):
    """Emitter that generates a PDF representation of the itinerary.
    
    AIDEV-NOTE: Uses a theme and components for flexible styling.
    """

    def __init__(self, theme: Optional[PDFTheme] = None):
        self.theme = theme or PDFTheme()
        self.event_component = EventComponent()

    def emit(self, itinerary: List[Event], output_path: str) -> str:
        """Write the itinerary to a PDF file."""
        path = Path(output_path)
        if not path.suffix:
            path = path.with_suffix(".pdf")
        
        path.parent.mkdir(parents=True, exist_ok=True)
        
        pdf = FPDF()
        pdf.add_page()
        
        # Title
        pdf.set_font(self.theme.fonts["heading"], "B", 16)
        pdf.cell(0, 10, "Trip Itinerary", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
        pdf.ln(10)
        
        for event in itinerary:
            self.event_component.render(pdf, self.theme, event)
        
        pdf.output(str(path))
        return str(path)

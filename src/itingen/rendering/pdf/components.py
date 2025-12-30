"""PDF rendering components for itinerary events.

AIDEV-NOTE: These components handle the layout and styling of specific 
itinerary elements (headings, details, descriptions) using the PDFTheme.
"""

from typing import List, Optional
from fpdf import FPDF
from itingen.rendering.pdf.themes import PDFTheme
from itingen.core.domain.events import Event


class PDFComponent:
    """Base class for PDF layout components."""
    
    def render(self, pdf: FPDF, theme: PDFTheme, data: Any):
        """Render the component to the PDF."""
        raise NotImplementedError


class EventComponent:
    """Renders a single event block."""

    def render(self, pdf: FPDF, theme: PDFTheme, event: Event):
        """Render the event block with its heading, details, and description."""
        # Event Heading
        pdf.set_font(theme.fonts["heading"], "B", 12)
        pdf.set_text_color(*self._hex_to_rgb(theme.colors["text"]))
        heading = event.event_heading or "Untitled Event"
        pdf.cell(0, 10, heading, ln=True)
        
        # Details
        pdf.set_font(theme.fonts["body"], "", 10)
        if event.kind:
            pdf.cell(0, 5, f"Kind: {event.kind}", ln=True)
        if event.location:
            pdf.cell(0, 5, f"Location: {event.location}", ln=True)
        if event.time_utc:
            pdf.cell(0, 5, f"Time (UTC): {event.time_utc}", ln=True)
        if event.who:
            pdf.cell(0, 5, f"Who: {', '.join(event.who)}", ln=True)
        
        # Description
        if event.description:
            pdf.ln(2)
            pdf.multi_cell(0, 5, event.description)
        
        # Travel To
        if event.travel_to:
            pdf.ln(2)
            pdf.set_font(theme.fonts["body"], "I", 10)
            pdf.cell(0, 5, "Travel To:", ln=True)
            pdf.set_font(theme.fonts["body"], "", 10)
            pdf.multi_cell(0, 5, event.travel_to)
        
        # Visual Separator
        pdf.ln(5)
        pdf.set_draw_color(*self._hex_to_rgb(theme.colors["primary"]))
        pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + 190, pdf.get_y())
        pdf.ln(5)

    def _hex_to_rgb(self, hex_color: str) -> tuple:
        """Convert hex color string to RGB tuple."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

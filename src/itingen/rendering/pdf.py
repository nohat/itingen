from typing import List
from pathlib import Path
from fpdf import FPDF
from itingen.core.base import BaseEmitter
from itingen.core.domain.events import Event

class PDFEmitter(BaseEmitter[Event]):
    """Emitter that generates a PDF representation of the itinerary."""

    def emit(self, itinerary: List[Event], output_path: str) -> bool:
        """Write the itinerary to a PDF file."""
        try:
            path = Path(output_path)
            if not path.suffix:
                path = path.with_suffix(".pdf")
            
            path.parent.mkdir(parents=True, exist_ok=True)
            
            pdf = FPDF()
            pdf.add_page()
            
            # Title
            pdf.set_font("helvetica", "B", 16)
            pdf.cell(0, 10, "Trip Itinerary", ln=True, align="C")
            pdf.ln(10)
            
            for event in itinerary:
                # Event Heading
                pdf.set_font("helvetica", "B", 12)
                heading = event.event_heading or "Untitled Event"
                pdf.cell(0, 10, heading, ln=True)
                
                # Details
                pdf.set_font("helvetica", "", 10)
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
                    pdf.set_font("helvetica", "I", 10)
                    pdf.cell(0, 5, "Travel To:", ln=True)
                    pdf.set_font("helvetica", "", 10)
                    pdf.multi_cell(0, 5, event.travel_to)
                
                pdf.ln(5)
                pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + 190, pdf.get_y())
                pdf.ln(5)
            
            pdf.output(str(path))
            return True
        except Exception as e:
            # In a real app we'd log this
            return False

"""PDF rendering components for itinerary events.

AIDEV-NOTE: These components handle the layout and styling of specific 
itinerary elements (headings, details, descriptions) using the PDFTheme.
"""

from typing import Any, Tuple
from pathlib import Path
from fpdf import FPDF
from itingen.rendering.pdf.themes import PDFTheme
from itingen.core.domain.events import Event
from itingen.rendering.timeline import TimelineDay
from itingen.utils.duration import format_duration

class PDFComponent:
    """Base class for PDF layout components."""
    
    def render(self, pdf: FPDF, theme: PDFTheme, data: Any):
        """Render the component to the PDF."""
        raise NotImplementedError

    def _hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """Convert hex color string to RGB tuple."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


class EventComponent(PDFComponent):
    """Renders a single event block with thumbnail support."""

    def render(self, pdf: FPDF, theme: PDFTheme, event: Event):
        """Render the event block with its heading, details, description, and thumbnail."""
        
        # Layout constants
        PAGE_WIDTH = pdf.epw
        IMAGE_SIZE = 35  # mm (square)
        TIME_WIDTH = 25  # mm
        PADDING = 4
        
        # Calculate available width for content
        # If image exists: PAGE_WIDTH - TIME_WIDTH - IMAGE_SIZE - PADDING*2
        # If no image: PAGE_WIDTH - TIME_WIDTH - PADDING
        
        has_image = bool(event.image_path and Path(event.image_path).exists())
        
        content_width = PAGE_WIDTH - TIME_WIDTH - PADDING
        if has_image:
            content_width -= (IMAGE_SIZE + PADDING)
            
        start_y = pdf.get_y()
        
        # --- Time Column (Left) ---
        pdf.set_font(theme.fonts["body"], "B", 10)
        pdf.set_text_color(*self._hex_to_rgb(theme.colors["text"]))
        
        time_str = "TBD"
        if event.time_local:
            try:
                if " " in event.time_local:
                    time_str = event.time_local.split(" ")[1]
                else:
                    time_str = event.time_local
                # Simple formatting: HH:MM:SS -> HH:MM
                if time_str.count(":") == 2:
                    time_str = ":".join(time_str.split(":")[:2])
            except Exception:
                pass
        
        pdf.cell(TIME_WIDTH, 5, time_str, ln=0)
        
        # Save X position for content
        content_x = pdf.get_x()
        
        # --- Image Column (Right) ---
        # We render image first if it exists to reserve space, or calculate layout?
        # Actually in FPDF layout flow, it's easier to place image absolutely or manage cursors.
        # Let's render content then place image? Or render image then content?
        # FPDF flow: we can set XY.
        
        if has_image:
            # Draw image at right margin
            image_x = pdf.w - pdf.r_margin - IMAGE_SIZE
            pdf.image(event.image_path, x=image_x, y=start_y, w=IMAGE_SIZE, h=IMAGE_SIZE)
        
        # --- Content Column (Middle) ---
        pdf.set_xy(content_x, start_y)
        
        # Heading
        pdf.set_font(theme.fonts["heading"], "B", 12)
        heading = event.event_heading or "Untitled Event"
        pdf.multi_cell(content_width, 6, heading)
        
        # Details (Location, Who)
        pdf.set_x(content_x)
        pdf.set_font(theme.fonts["body"], "", 9)
        pdf.set_text_color(*self._hex_to_rgb(theme.colors["text"]))
        
        details = []
        if event.location:
            # Sanitize Unicode characters for PDF compatibility
            location = event.location.replace("→", "->")
            details.append(f"Loc: {location}")
        if event.who:
            details.append(f"With: {', '.join(event.who)}")
        
        if details:
            pdf.multi_cell(content_width, 5, " | ".join(details))
            
        # Duration
        if getattr(event, "duration_seconds", None):
            duration_str = format_duration(event.duration_seconds)
            if duration_str:
                pdf.set_xy(pdf.l_margin, pdf.get_y()) # Go to left margin (under time)
                pdf.set_font(theme.fonts["body"], "I", 8)
                pdf.cell(TIME_WIDTH, 5, duration_str, ln=0)
                pdf.set_xy(content_x, pdf.get_y()) # Back to content column (same line)

        # Description
        if event.description:
            pdf.set_x(content_x)
            pdf.ln(1)
            pdf.set_font(theme.fonts["body"], "", 10)
            pdf.multi_cell(content_width, 5, event.description)
            
        # Narrative (AI Generated)
        if getattr(event, "narrative", None):
            pdf.set_x(content_x)
            pdf.ln(2)
            pdf.set_font(theme.fonts["body"], "I", 9)
            # Add a subtle border or background? For now just italics text
            pdf.set_text_color(80, 80, 80) # Dark gray
            pdf.multi_cell(content_width, 5, event.narrative)
            pdf.set_text_color(*self._hex_to_rgb(theme.colors["text"])) # Reset
            
        # Notes
        if getattr(event, "notes", None):
            pdf.set_x(content_x)
            pdf.ln(2)
            pdf.set_font(theme.fonts["body"], "B", 9)
            pdf.set_text_color(200, 0, 0) # Dark red for important notes
            pdf.multi_cell(content_width, 5, f"NOTE: {event.notes}")
            pdf.set_text_color(*self._hex_to_rgb(theme.colors["text"])) # Reset

        # Transition / Logistics
        if event.travel_to or event.transition_from_prev:
            pdf.set_x(content_x)
            pdf.ln(2)
            pdf.set_font(theme.fonts["body"], "", 9)
            trans_text = event.transition_from_prev or f"Travel to {event.travel_to}"
            pdf.multi_cell(content_width, 5, f"Transit: {trans_text}")

        # --- Footer / Spacing ---
        # Ensure we clear the image height
        current_y = pdf.get_y()
        if has_image:
            image_bottom = start_y + IMAGE_SIZE
            if current_y < image_bottom:
                pdf.set_y(image_bottom)
        
        pdf.ln(4)
        
        # Separator line
        pdf.set_draw_color(230, 230, 230) # Light gray
        pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
        pdf.ln(4)


class DayComponent(PDFComponent):
    """Renders a full day with header, banner, and events."""
    
    def __init__(self):
        self.event_component = EventComponent()

    def render(self, pdf: FPDF, theme: PDFTheme, day: TimelineDay):
        """Render the day block."""
        
        # Start new page for each day
        pdf.add_page()
        
        # --- Day Banner ---
        # If banner image exists, render it at top
        banner_height = 50 # mm ~ 16:9ish for page width
        
        if day.banner_image_path and Path(day.banner_image_path).exists():
            # Full width image
            pdf.image(day.banner_image_path, x=0, y=0, w=pdf.w, h=banner_height)
            pdf.set_y(banner_height + 5)
        else:
            # Just some space if no banner
            pdf.ln(10)
            
        # --- Day Title ---
        pdf.set_font(theme.fonts["heading"], "B", 18)
        pdf.set_text_color(*self._hex_to_rgb(theme.colors["primary"]))
        pdf.cell(0, 10, day.day_header, ln=True)
        pdf.ln(5)
        
        # --- Wake Up Info ---
        if day.wake_up_location:
            pdf.set_font(theme.fonts["body"], "", 10)
            pdf.set_text_color(*self._hex_to_rgb(theme.colors["text"]))
            pdf.cell(0, 6, f"Wake up: {day.wake_up_location}", ln=True)
            
        if day.first_event_target_time and day.first_event_title:
             pdf.set_font(theme.fonts["body"], "I", 9)
             pdf.cell(0, 6, f"   (Be ready by {day.first_event_target_time} for {day.first_event_title})", ln=True)
             
        pdf.ln(5)
        
        # --- Events ---
        for event in day.events:
            # Check for page break
            # Heuristic: if less than 40mm left, new page
            if pdf.h - pdf.get_y() - pdf.b_margin < 40:
                pdf.add_page()
                
            self.event_component.render(pdf, theme, event)
            
        # --- Sleep Info ---
        if day.sleep_location:
            # Ensure space
            if pdf.h - pdf.get_y() - pdf.b_margin < 20:
                pdf.add_page()
                
            pdf.ln(5)
            pdf.set_font(theme.fonts["body"], "B", 10)
            pdf.set_text_color(*self._hex_to_rgb(theme.colors["primary"]))
            pdf.cell(0, 10, f"Sleep at: {day.sleep_location}", ln=True, align="R")

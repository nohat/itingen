"""PDF rendering components for itinerary events.

AIDEV-NOTE: These components handle the layout and styling of specific 
itinerary elements using ReportLab's story-based rendering (not FPDF2).
"""

from typing import Any, List
from pathlib import Path
from xml.sax.saxutils import escape
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, Image, PageBreak, KeepTogether
from reportlab.lib.units import inch
from reportlab.lib import colors
from itingen.rendering.pdf.themes import PDFTheme
from itingen.core.domain.events import Event
from itingen.rendering.timeline import TimelineDay

class PDFComponent:
    """Base class for PDF layout components."""
    
    def render(self, story: List[Any], styles: Any, theme: PDFTheme, data: Any):
        """Render the component by appending flowables to the story."""
        raise NotImplementedError


class EventComponent(PDFComponent):
    """Renders a single event block with thumbnail support."""

    def render(self, story: List[Any], styles: Any, theme: PDFTheme, event: Event):
        """Render the event block by appending flowables to the story."""
        
        # Format time
        time_str = "TBD"
        if event.time_local:
            try:
                if " " in event.time_local:
                    time_str = event.time_local.split(" ")[1]
                else:
                    time_str = event.time_local
                if time_str.count(":") == 2:
                    time_str = ":".join(time_str.split(":")[:2])
            except Exception:
                pass
        
        # Build event content
        heading = event.event_heading or "Untitled Event"
        
        # Build details
        details = []
        if event.location:
            # Keep Unicode characters - ReportLab handles them
            details.append(f"<b>Location:</b> {escape(event.location)}")
        if event.who:
            details.append(f"<b>With:</b> {escape(', '.join(event.who))}")
        
        # Build table data: [time, content, image]
        content_parts = [f"<b>{escape(heading)}</b>"]
        
        if details:
            content_parts.append("<br/>".join(details))
        
        if event.description:
            content_parts.append(f"<br/>{escape(event.description)}")
        
        if getattr(event, "narrative", None):
            content_parts.append(f"<br/><i>{escape(event.narrative)}</i>")
        
        if getattr(event, "notes", None):
            content_parts.append(f"<br/><font color='red'><b>NOTE:</b> {escape(event.notes)}</font>")
        
        if event.travel_to or event.transition_from_prev:
            trans_text = event.transition_from_prev or f"Travel to {event.travel_to}"
            content_parts.append(f"<br/><i>Transit: {escape(trans_text)}</i>")
        
        content_html = "".join(content_parts)
        
        # Check for image
        has_image = bool(event.image_path and Path(event.image_path).exists())
        image_cell = ""
        if has_image:
            try:
                image_cell = Image(event.image_path, width=0.66*inch, height=0.66*inch)
            except Exception:
                image_cell = ""
        
        # Create table layout: [time | content | image]
        table_data = [[
            Paragraph(f"<b>{escape(time_str)}</b>", styles["event_details"]),
            Paragraph(content_html, styles["itinerary_body"]),
            image_cell,
        ]]
        
        col_widths = [0.8*inch, 5.2*inch, 0.8*inch] if has_image else [0.8*inch, 6.0*inch, 0]
        
        table = Table(table_data, colWidths=col_widths)
        table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LINEBELOW', (0, 0), (-1, -1), 1, colors.HexColor("#E5E7EB")),
        ]))
        
        story.append(KeepTogether([table, Spacer(1, 10)]))


class DayComponent(PDFComponent):
    """Renders a full day with header, banner, and events."""
    
    def __init__(self):
        self.event_component = EventComponent()

    def render(self, story: List[Any], styles: Any, theme: PDFTheme, day: TimelineDay):
        """Render the day block by appending flowables to the story."""
        
        # Start new page for each day
        story.append(PageBreak())
        
        # Day Banner (if exists)
        if day.banner_image_path and Path(day.banner_image_path).exists():
            try:
                # Full width banner image
                banner_img = Image(day.banner_image_path, width=6.5*inch, height=3.65*inch)
                story.append(banner_img)
                story.append(Spacer(1, 0.2*inch))
            except Exception:
                story.append(Spacer(1, 0.3*inch))
        else:
            story.append(Spacer(1, 0.3*inch))
        
        # Day Title and Weather
        title_para = Paragraph(escape(day.day_header), styles["day_header"])
        
        if day.weather_high is not None and day.weather_low is not None:
            # Weather summary box
            weather_text = f"<b>{int(day.weather_low)}°F - {int(day.weather_high)}°F</b>"
            if day.weather_conditions:
                weather_text += f"<br/>{escape(day.weather_conditions)}"
            
            weather_para = Paragraph(weather_text, styles["event_details"])
            
            # Use a table to layout Title and Weather box
            weather_table = Table(
                [[title_para, weather_para]],
                colWidths=[5.0*inch, 1.5*inch],
                style=TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
                    ('BACKGROUND', (1, 0), (1, 0), colors.HexColor("#F3F4F6")),
                    ('ROUNDEDCORNERS', [8, 8, 8, 8]),
                    ('LEFTPADDING', (1, 0), (1, 0), 8),
                    ('RIGHTPADDING', (1, 0), (1, 0), 8),
                    ('TOPPADDING', (1, 0), (1, 0), 6),
                    ('BOTTOMPADDING', (1, 0), (1, 0), 6),
                ])
            )
            story.append(weather_table)
        else:
            story.append(title_para)
            
        story.append(Spacer(1, 0.1*inch))
        
        # Wake Up Info
        if day.wake_up_location:
            story.append(Paragraph(f"<b>Wake up:</b> {escape(day.wake_up_location)}", styles["itinerary_body"]))
            
        if day.first_event_target_time and day.first_event_title:
            story.append(Paragraph(
                f"<i>(Be ready by {escape(day.first_event_target_time)} for {escape(day.first_event_title)})</i>",
                styles["itinerary_body"]
            ))
        
        story.append(Spacer(1, 0.15*inch))
        
        # Events
        for event in day.events:
            self.event_component.render(story, styles, theme, event)
        
        # Sleep Info
        if day.sleep_location:
            story.append(Spacer(1, 0.15*inch))
            story.append(Paragraph(
                f"<b>Sleep at:</b> {escape(day.sleep_location)}",
                styles["itinerary_body"]
            ))

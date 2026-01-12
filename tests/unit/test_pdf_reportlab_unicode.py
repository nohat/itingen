"""Tests for ReportLab PDF generation with Unicode support.

AIDEV-NOTE: These tests verify that the PDF renderer uses ReportLab (not FPDF2)
and properly handles Unicode characters like → (arrow) and Māori macrons.
"""

from itingen.core.domain.events import Event
from itingen.rendering.pdf.renderer import PDFEmitter


class TestReportLabUnicodeSupport:
    """Test that PDF renderer uses ReportLab and handles Unicode correctly."""

    def test_pdf_renderer_uses_reportlab(self, tmp_path):
        """Verify that PDFEmitter uses ReportLab, not FPDF2."""
        emitter = PDFEmitter()
        
        # Create a simple event with Unicode arrow
        events = [
            Event(
                event_heading="Travel",
                date="2025-01-01",
                time_utc="2025-01-01T10:00:00Z",
                location="Auckland → Wellington",
                description="Domestic flight"
            )
        ]
        
        output_path = tmp_path / "unicode_test.pdf"
        
        # This should NOT raise an error about unsupported characters
        emitter.emit(events, str(output_path))
         
        assert output_path.exists()
        assert output_path.stat().st_size > 0
        
        # Verify the PDF was created with ReportLab
        # ReportLab PDFs have specific markers in their structure
        with open(output_path, 'rb') as f:
            pdf_content = f.read()
            # ReportLab PDFs contain "/Producer (ReportLab PDF Library"
            assert b'ReportLab' in pdf_content

    def test_unicode_arrow_in_location(self, tmp_path):
        """Test that Unicode arrow (→) in location field renders correctly."""
        emitter = PDFEmitter()
        
        events = [
            Event(
                event_heading="Drive",
                date="2025-01-01",
                time_utc="2025-01-01T10:00:00Z",
                location="Queenstown → Gibbston Valley",
                description="Scenic drive"
            )
        ]
        
        output_path = tmp_path / "arrow_test.pdf"
        emitter.emit(events, str(output_path))
         
        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_maori_macrons_in_text(self, tmp_path):
        """Test that Māori macrons render correctly."""
        emitter = PDFEmitter()
        
        events = [
            Event(
                event_heading="Visit Māori Cultural Center",
                date="2025-01-01",
                time_utc="2025-01-01T10:00:00Z",
                location="Te Puia, Rotorua",
                description="Experience Māori culture and traditions"
            )
        ]
        
        output_path = tmp_path / "maori_test.pdf"
        emitter.emit(events, str(output_path))
         
        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_multiple_unicode_characters(self, tmp_path):
        """Test various Unicode characters in a single PDF."""
        emitter = PDFEmitter()
        
        events = [
            Event(
                event_heading="International Flight",
                date="2025-01-01",
                time_utc="2025-01-01T10:00:00Z",
                location="AKL → LAX",
                description="Return flight • 12h 30m"
            ),
            Event(
                event_heading="Māori Hangi",
                date="2025-01-01",
                time_utc="2025-01-01T18:00:00Z",
                location="Rotorua",
                description="Traditional feast with hāngī cooking"
            )
        ]
        
        output_path = tmp_path / "multi_unicode_test.pdf"
        emitter.emit(events, str(output_path))
         
        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_real_nz_trip_data_unicode(self, tmp_path):
        """Test with realistic NZ trip data containing Unicode."""
        emitter = PDFEmitter()
        
        # Simulate real data from trips/nz_2026/events/*.md
        events = [
            Event(
                event_heading="Drive to Gibbston Valley",
                date="2025-01-15",
                time_utc="2025-01-15T09:00:00Z",
                location="Queenstown → Gibbston Valley",
                description="Wine tasting tour"
            ),
            Event(
                event_heading="Transfer to Queenstown",
                date="2025-01-16",
                time_utc="2025-01-16T14:00:00Z",
                location="Te Anau → Queenstown",
                description="Scenic drive along Lake Wakatipu"
            ),
            Event(
                event_heading="Departure",
                date="2025-01-20",
                time_utc="2025-01-20T08:00:00Z",
                location="AKL → LAX",
                description="International departure"
            )
        ]
        
        output_path = tmp_path / "nz_trip_test.pdf"
        emitter.emit(events, str(output_path))
         
        assert output_path.exists()
        assert output_path.stat().st_size > 0

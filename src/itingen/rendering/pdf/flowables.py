"""Custom ReportLab flowables for scaffold-equivalent PDF rendering.

AIDEV-NOTE: Ported from scaffold nz_trip_pdf_render.py. Three flowables:
- KindIconCircle: colored circle with Material Icon glyph for event kind badge
- EventThumb: cover-scaled, rounded-corner thumbnail with border
- HeroBanner: full-width banner image with semi-transparent header + weather overlays
"""

import io
import os
from typing import Any, List, Optional

from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.platypus import Flowable, Table

from itingen.rendering.pdf.fonts import _material_icon_char
from itingen.rendering.pdf.themes import PDFTheme, kind_icon_color


class KindIconCircle(Flowable):
    """Colored circle with a Material Design icon glyph inside."""

    def __init__(
        self,
        *,
        kind: str,
        icon_name: str,
        theme: PDFTheme,
        size: float = 12.5,
    ):
        super().__init__()
        self._kind = kind
        self._icon_name = icon_name
        self._theme = theme
        self._size = size

    def wrap(self, availWidth, availHeight):
        return self._size, self._size

    def draw(self):
        c = self.canv
        r = self._size / 2

        fill = kind_icon_color(self._kind, self._theme)
        c.setFillColor(fill)
        c.setStrokeColor(fill)
        c.circle(r, r, r, stroke=0, fill=1)

        icon_char = ""
        if "MaterialIcons" in pdfmetrics.getRegisteredFontNames():
            icon_char = _material_icon_char(self._icon_name)

        font_name = (
            "MaterialIcons"
            if icon_char and "MaterialIcons" in pdfmetrics.getRegisteredFontNames()
            else "Helvetica-Bold"
        )
        glyph = icon_char if icon_char else (
            self._kind.strip()[:1].upper() if self._kind.strip() else "?"
        )

        font_size = self._size * (0.68 if icon_char else 0.56)
        c.setFillColor(colors.white)
        c.setFont(font_name, font_size)
        w = pdfmetrics.stringWidth(glyph, font_name, font_size)
        x = r - (w / 2)
        y = r - (font_size * 0.54)
        c.drawString(x, y, glyph)


class BannerImage(Flowable):
    """Banner image with "contain" scaling (no cropping)."""

    def __init__(self, *, path: str, width: float, height: float):
        super().__init__()
        self._path = path
        self._w = width
        self._h = height

    def wrap(self, availWidth, availHeight):
        return self._w, self._h

    def draw(self):
        c = self.canv
        w, h = self._w, self._h
        try:
            ir = ImageReader(self._path)
            iw, ih = ir.getSize()
        except Exception:
            return

        if iw <= 0 or ih <= 0:
            return
        scale = min(w / float(iw), h / float(ih))
        dw = float(iw) * scale
        dh = float(ih) * scale
        dx = (w - dw) / 2.0
        dy = (h - dh) / 2.0

        c.saveState()
        p = c.beginPath()
        p.rect(0, 0, w, h)
        c.clipPath(p, stroke=0, fill=0)
        c.drawImage(ir, dx, dy, width=dw, height=dh, mask="auto")
        c.restoreState()


class EventThumb(Flowable):
    """Cover-scaled thumbnail with rounded corners and border."""

    def __init__(self, *, path: str, size: float):
        super().__init__()
        self._path = path
        self._size = size

    def wrap(self, availWidth, availHeight):
        return self._size, self._size

    def draw(self):
        c = self.canv
        s = self._size

        if not self._path or not os.path.exists(self._path):
            return

        corner = max(1.5, float(s) * 0.12)

        try:
            ir_obj = None
            # Convert PNG to JPEG in-memory for PDF embedding.
            if str(self._path).lower().endswith(".png"):
                try:
                    from PIL import Image

                    buf = io.BytesIO()
                    im = Image.open(self._path)
                    if im.mode not in ("RGB", "L"):
                        im = im.convert("RGB")
                    im.save(buf, format="JPEG", quality=90, optimize=True)
                    buf.seek(0)
                    self._jpeg_buf = buf
                    ir_obj = ImageReader(buf)
                except Exception:
                    ir_obj = None

            if ir_obj is None:
                ir_obj = ImageReader(self._path)

            ir = ir_obj
            iw, ih = ir.getSize()
        except Exception:
            return

        if iw <= 0 or ih <= 0:
            return

        # "Cover" scale to fill the square, then center-crop.
        scale = max(s / float(iw), s / float(ih))
        dw = float(iw) * scale
        dh = float(ih) * scale
        dx = (s - dw) / 2.0
        dy = (s - dh) / 2.0

        c.saveState()
        p = c.beginPath()
        p.roundRect(0, 0, s, s, corner)
        c.clipPath(p, stroke=0, fill=0)
        c.setFillColor(colors.HexColor("#F8FAFC"))
        c.rect(0, 0, s, s, stroke=0, fill=1)
        c.drawImage(ir, dx, dy, width=dw, height=dh, mask="auto")
        c.restoreState()

        # Border stroke on top.
        c.saveState()
        c.setStrokeColor(colors.HexColor("#E5E7EB"))
        c.setLineWidth(0.6)
        c.roundRect(0, 0, s, s, corner, stroke=1, fill=0)
        c.restoreState()


class HeroBanner(Flowable):
    """Full-width banner image with semi-transparent header + weather overlays."""

    def __init__(
        self,
        *,
        banner_path: str,
        width: float,
        height: float,
        header_flowables: List[Any],
        weather_card: Optional[Table],
        theme: PDFTheme,
    ):
        super().__init__()
        self._banner_path = banner_path
        self._w = width
        self._h = height
        self._header_flowables = header_flowables
        self._weather_card = weather_card
        self._theme = theme

    def wrap(self, availWidth, availHeight):
        return self._w, self._h

    def draw(self):
        c = self.canv
        w, h = self._w, self._h

        # Draw banner image
        BannerImage(path=self._banner_path, width=w, height=h).drawOn(c, 0, 0)

        # Subtle white scrim
        c.saveState()
        c.setFillColor(colors.white)
        if hasattr(c, "setFillAlpha"):
            c.setFillAlpha(0.06)
        c.rect(0, 0, w, h, stroke=0, fill=1)
        c.restoreState()

        pad = 12
        corner = 9

        # Header overlay (top-left)
        header_max_w = min(w * 0.58, w - (pad * 2))
        header_y_top = h - pad
        header_total_h = 0.0
        for fl in self._header_flowables:
            try:
                _, hh = fl.wrap(header_max_w - (pad * 2), h)
            except Exception:
                hh = 0
            header_total_h += float(hh)
        header_box_h = header_total_h + (pad * 2)
        header_box_y = header_y_top - header_box_h

        c.saveState()
        c.setFillColor(colors.HexColor("#F8FAFC"))
        c.setStrokeColor(self._theme.line)
        c.setLineWidth(0.6)
        if hasattr(c, "setFillAlpha"):
            c.setFillAlpha(0.78)
        if hasattr(c, "setStrokeAlpha"):
            c.setStrokeAlpha(0.20)
        c.roundRect(pad, header_box_y, header_max_w, header_box_h, corner, stroke=1, fill=1)
        c.restoreState()

        cur_y = header_y_top - pad
        for fl in self._header_flowables:
            try:
                fw, fh = fl.wrap(header_max_w - (pad * 2), h)
                cur_y -= fh
                fl.drawOn(c, pad + pad, cur_y)
            except Exception:
                continue

        # Weather overlay (top-right)
        if self._weather_card is not None:
            weather_w = min(2.35 * inch, w * 0.34)
            weather_x = w - weather_w - pad
            try:
                _, weather_h = self._weather_card.wrap(weather_w - (pad * 2), h)
            except Exception:
                weather_h = 0
            weather_box_h = float(weather_h) + (pad * 2)
            weather_box_y = h - pad - weather_box_h

            c.saveState()
            c.setFillColor(colors.HexColor("#F8FAFC"))
            c.setStrokeColor(self._theme.line)
            c.setLineWidth(0.6)
            if hasattr(c, "setFillAlpha"):
                c.setFillAlpha(0.82)
            if hasattr(c, "setStrokeAlpha"):
                c.setStrokeAlpha(0.20)
            c.roundRect(weather_x, weather_box_y, weather_w, weather_box_h, corner, stroke=1, fill=1)
            c.restoreState()

            # Accent bar at top of weather card
            c.saveState()
            c.setFillColor(self._theme.accent)
            if hasattr(c, "setFillAlpha"):
                c.setFillAlpha(0.90)
            c.roundRect(weather_x, weather_box_y + weather_box_h - 6, weather_w, 6, corner, stroke=0, fill=1)
            c.restoreState()

            try:
                self._weather_card.wrapOn(c, weather_w - (pad * 2), weather_box_h - (pad * 2))
                self._weather_card.drawOn(c, weather_x + pad, weather_box_y + pad)
            except Exception:
                pass

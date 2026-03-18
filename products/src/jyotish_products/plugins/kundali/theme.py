"""Sanatan Dharma aesthetic theme — colors, fonts, and PDF styles.

Provides a unified visual identity for all kundali PDF renderers.
Every renderer imports constants from here instead of defining its own.
"""
from __future__ import annotations

from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


# ── Sanatan Dharma color palette ─────────────────────────────────────────
SAFFRON = HexColor("#FF6F00")
CREAM = HexColor("#FFFDE7")
DEEP_GREEN = HexColor("#2E7D32")
DEEP_RED = HexColor("#C62828")
GOLD = HexColor("#FF8F00")
INDIGO = HexColor("#1A237E")
LIGHT_SAFFRON = HexColor("#FFF3E0")
SUBTLE_GRAY = HexColor("#F5F5F5")
TEXT_DARK = HexColor("#212121")
TEXT_LIGHT = HexColor("#757575")

# Matplotlib-compatible hex strings (no HexColor wrapper)
MPL_SAFFRON = "#FF6F00"
MPL_CREAM = "#FFFDE7"
MPL_GREEN = "#2E7D32"
MPL_RED = "#C62828"
MPL_GOLD = "#FF8F00"
MPL_INDIGO = "#1A237E"
MPL_TEXT = "#212121"
MPL_GRAY = "#9E9E9E"

# ── Font registration ────────────────────────────────────────────────────
_FONT_DIR = Path(__file__).parent.parent.parent.parent.parent.parent / "assets" / "fonts"
_FONT_REGISTERED = False


def _find_font_path() -> Path | None:
    """Locate NotoSansDevanagari.ttf in known locations."""
    candidates = [
        _FONT_DIR / "NotoSansDevanagari.ttf",
        Path("assets/fonts/NotoSansDevanagari.ttf"),
        Path(__file__).parent / "NotoSansDevanagari.ttf",
    ]
    for p in candidates:
        if p.exists():
            return p
    return None


def register_fonts() -> bool:
    """Register NotoSansDevanagari with ReportLab. Safe to call multiple times.

    Returns:
        True if Devanagari font is available, False if fallback to Helvetica.
    """
    global _FONT_REGISTERED
    if _FONT_REGISTERED:
        return True

    font_path = _find_font_path()
    if font_path is None:
        return False

    try:
        pdfmetrics.registerFont(TTFont("NotoDevanagari", str(font_path)))
        _FONT_REGISTERED = True
        return True
    except Exception:
        return False


def get_font_path() -> Path | None:
    """Return the font file path for matplotlib usage."""
    return _find_font_path()


# ── ReportLab paragraph styles ───────────────────────────────────────────

def pdf_styles() -> dict[str, ParagraphStyle]:
    """Create themed paragraph styles for the kundali PDF.

    Call register_fonts() before using these styles.
    """
    ss = getSampleStyleSheet()
    font = "NotoDevanagari" if _FONT_REGISTERED else "Helvetica"

    return {
        "title": ParagraphStyle(
            "KTitle", parent=ss["Title"], fontName=font,
            fontSize=24, textColor=INDIGO, spaceAfter=12, alignment=1,
        ),
        "subtitle": ParagraphStyle(
            "KSubtitle", parent=ss["Normal"], fontName=font,
            fontSize=14, textColor=SAFFRON, spaceAfter=8, alignment=1,
        ),
        "h1": ParagraphStyle(
            "KH1", parent=ss["Heading1"], fontName=font,
            fontSize=16, textColor=INDIGO, spaceAfter=8, spaceBefore=14,
        ),
        "h2": ParagraphStyle(
            "KH2", parent=ss["Heading2"], fontName=font,
            fontSize=13, textColor=SAFFRON, spaceAfter=6, spaceBefore=10,
        ),
        "body": ParagraphStyle(
            "KBody", parent=ss["Normal"], fontName=font,
            fontSize=10, textColor=TEXT_DARK, spaceAfter=4, leading=14,
        ),
        "body_hi": ParagraphStyle(
            "KBodyHi", parent=ss["Normal"], fontName=font,
            fontSize=11, textColor=TEXT_DARK, spaceAfter=4, leading=16,
        ),
        "small": ParagraphStyle(
            "KSmall", parent=ss["Normal"], fontName=font,
            fontSize=8, textColor=TEXT_LIGHT, leading=10,
        ),
        "footer": ParagraphStyle(
            "KFooter", parent=ss["Normal"], fontName=font,
            fontSize=7, textColor=TEXT_LIGHT, alignment=1,
        ),
        "om": ParagraphStyle(
            "KOm", parent=ss["Title"], fontName=font,
            fontSize=48, textColor=SAFFRON, alignment=1, spaceAfter=20,
        ),
    }


# ── Devanagari planet abbreviations ──────────────────────────────────────
PLANET_HI: dict[str, str] = {
    "Sun": "सू", "Moon": "चं", "Mars": "मं", "Mercury": "बु",
    "Jupiter": "गु", "Venus": "शु", "Saturn": "श", "Rahu": "रा", "Ketu": "के",
}

PLANET_EN_SHORT: dict[str, str] = {
    "Sun": "Su", "Moon": "Mo", "Mars": "Ma", "Mercury": "Me",
    "Jupiter": "Ju", "Venus": "Ve", "Saturn": "Sa", "Rahu": "Ra", "Ketu": "Ke",
}

# ── House labels (Hindi) ────────────────────────────────────────────────
HOUSE_LABEL_HI: dict[int, str] = {
    1: "तनु", 2: "धन", 3: "सहज", 4: "सुख",
    5: "सन्तान", 6: "रोग", 7: "जाया", 8: "मृत्यु",
    9: "भाग्य", 10: "कर्म", 11: "लाभ", 12: "व्यय",
}

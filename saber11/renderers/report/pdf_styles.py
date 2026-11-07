"""Shared ReportLab styles (black and white, Arial, justified text), table and figure builders."""

from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Image, KeepTogether, Paragraph, Table, TableStyle

from saber11.renderers.report.pdf_fonts import FONTS

REGULAR, BOLD = FONTS.regular, FONTS.bold
BODY = ParagraphStyle("Body", fontName=REGULAR, bulletFontName=REGULAR, fontSize=10, leading=14,
                      alignment=TA_JUSTIFY, spaceAfter=4)
H1 = ParagraphStyle("H1", fontName=BOLD, fontSize=15, leading=19, spaceBefore=12, spaceAfter=8, keepWithNext=1)
H2 = ParagraphStyle("H2", fontName=BOLD, fontSize=11.5, leading=15, spaceBefore=10, spaceAfter=4, keepWithNext=1)
TITLE = ParagraphStyle("Title", fontName=BOLD, fontSize=24, leading=30, alignment=TA_CENTER, spaceAfter=18)
SUBTITLE = ParagraphStyle("Subtitle", parent=BODY, alignment=TA_CENTER)
CAPTION = ParagraphStyle("Caption", parent=BODY, fontSize=8.5, leading=11, alignment=TA_CENTER, spaceAfter=8)
CELL = ParagraphStyle("Cell", fontName=REGULAR, fontSize=8, leading=10, alignment=TA_LEFT)
CELL_BOLD = ParagraphStyle("CellBold", parent=CELL, fontName=BOLD)
TEXT_WIDTH = 21.0 * cm - 2 * 40  # A4 width minus the document margins
# Black and white only: lines, no fills.
TABLE_STYLE = (
    ("GRID", (0, 0), (-1, -1), 0.4, colors.black),
    ("LINEBELOW", (0, 0), (-1, 0), 1.0, colors.black),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
)


def para(text: str, style: ParagraphStyle = BODY) -> Paragraph:
    """Build a paragraph."""
    return Paragraph(text, style)


def bullet(text: str) -> Paragraph:
    """Build a bulleted, justified paragraph."""
    return Paragraph(text, BODY, bulletText="-")


def make_table(rows: list[list[str]], bold_rows: tuple[int, ...] = (), col_widths=None) -> Table:
    """Build a black-and-white table with a bold, repeating header; bold_rows exclude the header."""
    head = [Paragraph(str(c), CELL_BOLD) for c in rows[0]]
    body = [[Paragraph(str(c), CELL_BOLD if i in bold_rows else CELL) for c in r]
            for i, r in enumerate(rows[1:])]
    table = Table([head, *body], colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle(list(TABLE_STYLE)))
    return table


def figure(png: bytes, caption: str, width: float = TEXT_WIDTH) -> KeepTogether:
    """Embed a PNG at `width`, keeping its aspect ratio, with a caption below."""
    w, h = ImageReader(BytesIO(png)).getSize()
    image = Image(BytesIO(png), width=width, height=width * h / w)
    return KeepTogether([image, Paragraph(caption, CAPTION)])


def draw_footer(canvas, doc) -> None:
    """Draw the page number in the footer."""
    canvas.saveState()
    canvas.setFont(REGULAR, 8)
    canvas.drawCentredString(doc.pagesize[0] / 2, 20, f"Página {doc.page}")
    canvas.restoreState()

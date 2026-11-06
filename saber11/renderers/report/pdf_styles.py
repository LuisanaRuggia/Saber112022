"""Shared ReportLab styles, table builder and page footer."""

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, Table, TableStyle

_BASE = getSampleStyleSheet()
BODY = ParagraphStyle("Body", parent=_BASE["BodyText"], fontSize=10, leading=14)
H1 = ParagraphStyle("H1", parent=_BASE["Heading1"], fontSize=16, spaceBefore=12, spaceAfter=8)
H2 = ParagraphStyle("H2", parent=_BASE["Heading2"], fontSize=12, spaceBefore=10, spaceAfter=4)
TITLE = ParagraphStyle("Title2", parent=_BASE["Title"], fontSize=26, leading=32, spaceAfter=18)
CELL = ParagraphStyle("Cell", parent=BODY, fontSize=8, leading=10)
CELL_BOLD = ParagraphStyle("CellBold", parent=CELL, fontName="Helvetica-Bold")
_HEADER_BG = colors.HexColor("#1f3a5f")


def para(text: str, style: ParagraphStyle = BODY) -> Paragraph:
    """Build a paragraph."""
    return Paragraph(text, style)


def bullet(text: str) -> Paragraph:
    """Build a bulleted paragraph."""
    return Paragraph(text, BODY, bulletText="-")


def make_table(rows: list[list[str]], bold_rows: tuple[int, ...] = (), col_widths=None) -> Table:
    """Build a repeating-header table; row indexes in bold_rows exclude the header."""
    head = [Paragraph(f"<b>{c}</b>", CELL) for c in rows[0]]
    body = [[Paragraph(str(c), CELL_BOLD if i in bold_rows else CELL) for c in r]
            for i, r in enumerate(rows[1:])]
    table = Table([head, *body], colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#dfe7f2")),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f7fa")]),
    ]))
    return table


def draw_footer(canvas, doc) -> None:
    """Draw the page number in the footer."""
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.drawCentredString(doc.pagesize[0] / 2, 20, f"Página {doc.page}")
    canvas.restoreState()

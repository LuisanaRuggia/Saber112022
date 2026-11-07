"""Register Arial for the PDF, falling back to Liberation Sans (same metrics) when Arial is absent.

Arial is proprietary and not shipped with most Linux systems; `ttf-mscorefonts-installer` provides it.
Liberation Sans is metrically identical, so the layout does not change between the two.
"""

from dataclasses import dataclass
from pathlib import Path

from reportlab.lib.fonts import addMapping
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

FONT_DIRS = (Path("/usr/share/fonts/truetype/msttcorefonts"), Path("/usr/share/fonts/truetype/liberation"),
             Path("/usr/share/fonts/truetype/liberation2"), Path("/usr/share/fonts/TTF"),
             Path("/Library/Fonts"), Path("C:/Windows/Fonts"))
CANDIDATES = (("Arial", "Arial.ttf", "Arial_Bold.ttf"), ("Arial", "arial.ttf", "arialbd.ttf"),
              ("Liberation Sans", "LiberationSans-Regular.ttf", "LiberationSans-Bold.ttf"))


@dataclass(frozen=True)
class Fonts:
    """Font names registered in ReportLab."""

    family: str   # human name, also used by matplotlib
    regular: str
    bold: str


def _find(regular: str, bold: str) -> tuple[Path, Path] | None:
    for folder in FONT_DIRS:
        if (folder / regular).is_file() and (folder / bold).is_file():
            return folder / regular, folder / bold
    return None


def register_fonts() -> Fonts:
    """Register the first available Arial-compatible family; Helvetica (built in) as last resort."""
    for family, regular, bold in CANDIDATES:
        found = _find(regular, bold)
        if found is None:
            continue
        names = ("ReportSans", "ReportSans-Bold")
        pdfmetrics.registerFont(TTFont(names[0], str(found[0])))
        pdfmetrics.registerFont(TTFont(names[1], str(found[1])))
        addMapping(names[0], 0, 0, names[0])
        addMapping(names[0], 1, 0, names[1])
        return Fonts(family, *names)
    return Fonts("Helvetica", "Helvetica", "Helvetica-Bold")


FONTS = register_fonts()

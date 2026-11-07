"""Matplotlib setup shared by every chart of the report: color marks, black text."""

from io import BytesIO

import matplotlib

matplotlib.use("Agg")  # headless: charts are rendered to PNG bytes, never shown

import matplotlib.pyplot as plt  # noqa: E402

from saber11.renderers.report.pdf_fonts import FONTS  # noqa: E402

# Categorical palette in fixed order, validated for color-vision deficiency (adjacent ΔE >= 9).
SERIES = ("#2a78d6", "#eb6834", "#1baf7a", "#eda100")
# Color follows the shift, never its rank: every chart paints a shift the same way.
SHIFT_COLORS = dict(zip(("COMPLETA", "MAÑANA", "TARDE", "UNICA"), SERIES))
NEUTRAL = "#52514e"   # reference lines
REGION = "#d9d8d4"    # rejection regions
SEQUENTIAL = "Blues"  # one hue, light to dark, for magnitudes
DPI = 200

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": [FONTS.family, "Arial", "Liberation Sans", "DejaVu Sans"],
    "font.size": 9,
    "axes.edgecolor": "black",
    "axes.labelcolor": "black",
    "axes.prop_cycle": matplotlib.cycler(color=list(SERIES)),
    "axes.axisbelow": True,
    "xtick.color": "black",
    "ytick.color": "black",
    "text.color": "black",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "legend.frameon": False,
})


def bar_style(index: int) -> dict:
    """Return the fill of the index-th series with a thin white gap between adjacent bars."""
    return {"color": SERIES[index % len(SERIES)], "edgecolor": "white", "linewidth": 0.8}


def shift_colors(shifts) -> list[str]:
    """Return the fixed color of each shift code."""
    return [SHIFT_COLORS.get(s, NEUTRAL) for s in shifts]


def to_png(fig) -> bytes:
    """Render a figure to PNG bytes and release it."""
    buffer = BytesIO()
    fig.savefig(buffer, format="png", dpi=DPI, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return buffer.getvalue()

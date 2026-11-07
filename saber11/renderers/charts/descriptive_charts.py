"""Charts of the descriptive section: means, dispersion and the correlation matrix."""

import numpy as np
import pandas as pd

from saber11.models.dataset.dataset_models import SCORE_SHORT_LABELS, SCORES, SHIFT_LABELS
from saber11.renderers.charts.chart_style import SEQUENTIAL, SHIFT_COLORS, plt, to_png


def _grouped_bars(table: pd.DataFrame, ylabel: str, bottom: float | None = None) -> bytes:
    """Draw one group of bars per score and one bar per shift."""
    fig, ax = plt.subplots(figsize=(7.5, 3.2))
    x, width = np.arange(len(SCORES)), 0.8 / len(table.index)
    for i, shift in enumerate(table.index):
        offset = (i - (len(table.index) - 1) / 2) * width
        ax.bar(x + offset, table.loc[shift, list(SCORES)], width, label=SHIFT_LABELS.get(shift, shift),
               color=SHIFT_COLORS[shift], edgecolor="white", linewidth=0.8)
    ax.set_xticks(x, [SCORE_SHORT_LABELS[s] for s in SCORES])
    ax.set_ylabel(ylabel)
    if bottom is not None:
        ax.set_ylim(bottom=bottom)
    ax.legend(ncols=len(table.index), loc="upper center", bbox_to_anchor=(0.5, 1.15))
    return to_png(fig)


def means_chart(means: pd.DataFrame) -> bytes:
    """Mean score per shift and test."""
    return _grouped_bars(means, "Puntaje medio", bottom=max(0.0, float(means.min().min()) - 10))


def dispersion_chart(std: pd.DataFrame) -> bytes:
    """Standard deviation per shift and test (the diagonal Box's M compares)."""
    return _grouped_bars(std, "Desviación estándar", bottom=0.0)


def correlation_heatmap(correlation: pd.DataFrame) -> bytes:
    """Single-hue heatmap of the correlation matrix with the values written in each cell."""
    labels = [SCORE_SHORT_LABELS[s] for s in correlation.columns]
    fig, ax = plt.subplots(figsize=(4.6, 3.8))
    image = ax.imshow(correlation.to_numpy(), cmap=SEQUENTIAL, vmin=0, vmax=1)
    for (i, j), value in np.ndenumerate(correlation.to_numpy()):
        ax.text(j, i, f"{value:.2f}".replace(".", ","), ha="center", va="center",
                color="white" if value > 0.6 else "black", fontsize=8)
    ax.set_xticks(range(len(labels)), labels)
    ax.set_yticks(range(len(labels)), labels)
    ax.spines[:].set_visible(False)
    fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04, label="Correlación")
    return to_png(fig)

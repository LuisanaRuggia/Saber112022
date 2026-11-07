"""Charts of the explanatory, sensitivity and spatial results."""

import numpy as np
import pandas as pd

from saber11.models.analysis.analysis_models import PcaResult
from saber11.models.dataset.dataset_models import SHIFT_LABELS
from saber11.renderers.charts.chart_style import NEUTRAL, SERIES, plt, shift_colors, to_png


def pca_chart(pca: PcaResult) -> bytes:
    """Scree plot of the eigenvalues and mean PC1 score per shift."""
    fig, (scree, means) = plt.subplots(1, 2, figsize=(8, 3.2))
    components = np.arange(1, len(pca.eigenvalues) + 1)
    scree.plot(components, pca.eigenvalues, color=SERIES[0], marker="o", markersize=6, lw=2)
    scree.axhline(1, color=NEUTRAL, ls=":", lw=1, label="Autovalor = 1")
    scree.set(title="Autovalores", xlabel="Componente", ylabel="Autovalor", xticks=components)
    scree.legend(fontsize=7)
    shifts = list(pca.cp1_means)
    values = [pca.cp1_means[s] for s in shifts]
    means.bar([SHIFT_LABELS.get(s, s) for s in shifts], values, color=shift_colors(shifts), edgecolor="white")
    means.axhline(0, color=NEUTRAL, lw=0.8)
    means.set(title="Media del CP1 por jornada", ylabel="Media del puntaje en el CP1")
    fig.tight_layout()
    return to_png(fig)


def private_share_chart(profile: pd.DataFrame) -> bytes:
    """Share of private-school students in each shift."""
    shares = profile["share_private"].fillna(0) * 100
    fig, ax = plt.subplots(figsize=(6, 2.6))
    bars = ax.bar([SHIFT_LABELS.get(s, s) for s in shares.index], shares, color=shift_colors(shares.index),
                  edgecolor="white")
    ax.bar_label(bars, labels=[f"{v:.1f} %".replace(".", ",") for v in shares], fontsize=8)
    ax.set(ylabel="% de estudiantes en colegios privados", ylim=(0, 110))
    return to_png(fig)


def locality_chart(table: pd.DataFrame) -> bytes:
    """Average of the five tests per locality, best at the top."""
    ordered = table.sort_values("avg_5")
    fig, ax = plt.subplots(figsize=(7, 0.28 * len(ordered) + 0.8))
    ax.barh(ordered["localidad"], ordered["avg_5"], color=SERIES[0], edgecolor="white")
    ax.set_xlim(left=max(0.0, float(ordered["avg_5"].min()) - 5))
    ax.set_xlabel("Promedio de las 5 pruebas")
    ax.tick_params(axis="y", labelsize=8)
    return to_png(fig)

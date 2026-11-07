"""Mardia's multivariate normality chart: reference distributions, p-values by shift and a χ² Q-Q plot."""

import numpy as np
from scipy import stats

from saber11.models.analysis.analysis_models import AssumptionsResult
from saber11.models.dataset.dataset_models import SCORES, SHIFT_LABELS
from saber11.renderers.charts.chart_style import NEUTRAL, REGION, SERIES, bar_style, plt, to_png

P = len(SCORES)
SKEW_DF = P * (P + 1) * (P + 2) / 6


def _observed(ax, guide: float, within: float) -> None:
    ax.axvline(guide, color=SERIES[0], ls="--", lw=2, label=f"Guía = {guide:.2f}".replace(".", ","))
    ax.axvline(within, color=SERIES[1], ls=":", lw=2, label=f"Residuos = {within:.2f}".replace(".", ","))


def _skewness(ax, a: AssumptionsResult, alpha: float) -> None:
    x = np.linspace(0, max(90.0, a.mardia.skewness_stat * 1.2), 400)
    density = stats.chi2.pdf(x, SKEW_DF)
    ax.plot(x, density, color=NEUTRAL, lw=1.2)
    ax.fill_between(x, density, where=x >= stats.chi2.ppf(1 - alpha, SKEW_DF), color=REGION, label="Rechazo")
    _observed(ax, a.mardia.skewness_stat, a.mardia_within.skewness_stat)
    ax.set(title=f"Asimetría vs χ²({SKEW_DF:.0f})", xlabel="Estadístico", ylabel="Densidad")
    ax.legend(fontsize=7)


def _kurtosis(ax, a: AssumptionsResult, alpha: float) -> None:
    z = np.linspace(-4, 4, 400)
    density = stats.norm.pdf(z)
    ax.plot(z, density, color=NEUTRAL, lw=1.2)
    ax.fill_between(z, density, where=np.abs(z) >= stats.norm.ppf(1 - alpha / 2), color=REGION, label="Rechazo")
    _observed(ax, a.mardia.kurtosis_stat, a.mardia_within.kurtosis_stat)
    ax.set(title="Curtosis vs N(0, 1)", xlabel="z", ylabel="Densidad")
    ax.legend(fontsize=7)


def _by_group(ax, a: AssumptionsResult, alpha: float) -> None:
    shifts = list(a.mardia.by_group)
    x = np.arange(len(shifts))
    for i, label in enumerate(("Asimetría", "Curtosis")):
        values = [max(a.mardia.by_group[s][i], 1e-6) for s in shifts]
        ax.bar(x + (i - 0.5) * 0.4, values, 0.4, label=label, **bar_style(i))
    ax.axhline(alpha, color=NEUTRAL, ls="--", lw=1, label=f"α = {alpha}".replace(".", ","))
    ax.set_yscale("log")
    ax.set_xticks(x, [SHIFT_LABELS.get(s, s) for s in shifts])
    ax.set(title="p-valor por jornada (escala log)", ylabel="p-valor")
    ax.legend(fontsize=7)


def _qq(ax, a: AssumptionsResult) -> None:
    observed = np.sort(np.asarray(a.mahalanobis_within.squared_distances))
    expected = stats.chi2.ppf((np.arange(1, len(observed) + 1) - 0.5) / len(observed), P)
    ax.scatter(expected, observed, s=10, color=SERIES[0], edgecolor="white", linewidth=0.3)
    top = float(expected.max()) if len(expected) else 1.0
    ax.plot([0, top], [0, top], color=NEUTRAL, lw=1.2, label="Normal multivariada")
    ax.axhline(a.mahalanobis_within.threshold, color=SERIES[1], ls=":", lw=1.5, label="Umbral de atípicos")
    ax.set(title=f"Q-Q χ²({P}) de distancias (residuos)", xlabel="Cuantil teórico", ylabel="Distancia² observada")
    ax.legend(fontsize=7)


def mardia_chart(assumptions: AssumptionsResult, alpha: float) -> bytes:
    """Four panels that show where the multivariate normality checks land."""
    fig, axes = plt.subplots(2, 2, figsize=(8, 6.4))
    _skewness(axes[0, 0], assumptions, alpha)
    _kurtosis(axes[0, 1], assumptions, alpha)
    _by_group(axes[1, 0], assumptions, alpha)
    _qq(axes[1, 1], assumptions)
    fig.tight_layout()
    return to_png(fig)

"""Descriptive analysis and assumptions sections."""

import pandas as pd

from saber11.core.formatting.spanish_numbers import fmt_num, fmt_p
from saber11.models.dataset.dataset_models import SCORE_LABELS, SCORES, SHIFT_LABELS
from saber11.models.report.report_models import PipelineResults
from saber11.renderers.report.pdf_styles import H1, H2, make_table, para

_SHORT = {s: SCORE_LABELS[s] for s in SCORES}


def _matrix(df: pd.DataFrame, decimals: int) -> list[list[str]]:
    rows = [[""] + [_SHORT[c] for c in df.columns]]
    return rows + [[_SHORT.get(i, i), *[fmt_num(v, decimals) for v in df.loc[i]]] for i in df.index]


def _means_rows(means: pd.DataFrame, std: pd.DataFrame | None) -> list[list[str]]:
    rows = [["Jornada", *[_SHORT[s] for s in SCORES]]]
    for g in means.index:
        cells = [f"{fmt_num(means.loc[g, s], 1)} ({fmt_num(std.loc[g, s], 1)})" if std is not None
                 else fmt_num(means.loc[g, s], 1) for s in SCORES]
        rows.append([SHIFT_LABELS.get(g, g), *cells])
    return rows


def descriptive_section(results: PipelineResults) -> list:
    """Build section 3."""
    d = results.descriptive
    n_rows = [["Jornada", "n muestra", "n población"]] + [
        [SHIFT_LABELS.get(g, g), fmt_num(n, 0), fmt_num(d.population_n_by_group.get(g, 0), 0)]
        for g, n in d.n_by_group.items()]
    return [para("3. Análisis descriptivo", H1), para("Tamaño por grupo", H2), make_table(n_rows),
            para("Medias (desviación estándar) de la muestra", H2), make_table(_means_rows(d.means, d.std)),
            para("Medias de la población de Bogotá", H2), make_table(_means_rows(d.population_means, None)),
            para("Matriz de covarianzas (muestra)", H2), make_table(_matrix(d.covariance, 1)),
            para("Matriz de correlaciones (muestra)", H2), make_table(_matrix(d.correlation, 3))]


def assumptions_section(results: PipelineResults) -> list:
    """Build section 4."""
    a, alpha = results.assumptions, results.metadata.alpha
    mah, mar, box = a.mahalanobis, a.mardia, a.box_m
    ok = lambda p: "No se rechaza" if p >= alpha else "Se rechaza"  # noqa: E731
    rows = [["Prueba", "Estadístico", "p", "Decisión"],
            ["Mahalanobis (umbral χ²)", f"{fmt_num(mah.threshold, 2)}; atípicos: {mah.n_outliers} "
             f"({fmt_num(mah.pct_outliers, 1)} %)", "-", "Informativo"],
            ["Mardia asimetría (global)", fmt_num(mar.skewness_stat, 2), fmt_p(mar.skewness_p), ok(mar.skewness_p)],
            ["Mardia curtosis (global)", fmt_num(mar.kurtosis_stat, 2), fmt_p(mar.kurtosis_p), ok(mar.kurtosis_p)]]
    for g, (ps, pk) in mar.by_group.items():
        label = SHIFT_LABELS.get(g, g)
        rows.append([f"Mardia asimetría, {label}", "-", fmt_p(ps), ok(ps)])
        rows.append([f"Mardia curtosis, {label}", "-", fmt_p(pk), ok(pk)])
    rows.append(["M de Box", f"χ² = {fmt_num(box.chi2, 2)} (gl = {box.df})", fmt_p(box.p_value), ok(box.p_value)])
    return [para("4. Supuestos", H1), make_table(rows)]

"""Descriptive analysis and assumptions sections."""

import pandas as pd

from saber11.core.formatting.spanish_numbers import fmt_num, fmt_p
from saber11.models.dataset.dataset_models import SCORE_LABELS, SCORES, SHIFT_LABELS
from saber11.models.report.report_models import PipelineResults
from saber11.renderers.charts.assumption_charts import mardia_chart
from saber11.renderers.charts.descriptive_charts import correlation_heatmap, dispersion_chart, means_chart
from saber11.renderers.report.pdf_styles import H1, H2, figure, make_table, para

def _matrix(df: pd.DataFrame, decimals: int) -> list[list[str]]:
    rows = [[""] + [SCORE_LABELS[c] for c in df.columns]]
    return rows + [[SCORE_LABELS.get(i, i), *[fmt_num(v, decimals) for v in df.loc[i]]] for i in df.index]


def _means_rows(means: pd.DataFrame, std: pd.DataFrame | None) -> list[list[str]]:
    rows = [["Jornada", *[SCORE_LABELS[s] for s in SCORES]]]
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
            figure(means_chart(d.means), "Figura 1. Puntaje medio por jornada y prueba (muestra)."),
            para("Medias de la población de Bogotá", H2), make_table(_means_rows(d.population_means, None)),
            para("Matriz de covarianzas (muestra)", H2), make_table(_matrix(d.covariance, 1)),
            para("Matriz de correlaciones (muestra)", H2), make_table(_matrix(d.correlation, 3)),
            figure(correlation_heatmap(d.correlation), "Figura 2. Matriz de correlaciones entre pruebas (muestra).",
                   width=280)]


WITHIN_NOTE = ("La guía calcula Mahalanobis y Mardia con la covarianza total, que mezcla las diferencias entre "
               "jornadas con la variación de los estudiantes. El MANOVA supone normalidad de los residuos dentro de "
               "cada jornada, por eso también se reportan sobre los residuos con la covarianza combinada.")


def _within_rows(a, alpha: float) -> list[list[str]]:
    mah, mar = a.mahalanobis_within, a.mardia_within
    ok = lambda p: "No se rechaza" if p >= alpha else "Se rechaza"  # noqa: E731
    return [["Prueba", "Estadístico", "p", "Decisión"],
            ["Mahalanobis (umbral χ²)", f"{fmt_num(mah.threshold, 2)}; atípicos: {mah.n_outliers} "
             f"({fmt_num(mah.pct_outliers, 1)} %)", "-", "Informativo"],
            ["Mardia asimetría (residuos)", fmt_num(mar.skewness_stat, 2), fmt_p(mar.skewness_p), ok(mar.skewness_p)],
            ["Mardia curtosis (residuos)", fmt_num(mar.kurtosis_stat, 2), fmt_p(mar.kurtosis_p), ok(mar.kurtosis_p)]]


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
    return [para("4. Supuestos", H1), para("Método de la guía (covarianza total)", H2), make_table(rows),
            para("Dentro de jornadas (residuos y covarianza combinada)", H2), make_table(_within_rows(a, alpha)),
            para(WITHIN_NOTE),
            figure(mardia_chart(a, alpha), "Figura 3. Normalidad multivariada de Mardia: estadísticos frente a su "
                   "distribución de referencia, p-valor por jornada y gráfico Q-Q de las distancias de Mahalanobis."),
            figure(dispersion_chart(results.descriptive.std), "Figura 4. Desviación estándar por jornada y prueba: "
                   "la dispersión que compara la M de Box.")]

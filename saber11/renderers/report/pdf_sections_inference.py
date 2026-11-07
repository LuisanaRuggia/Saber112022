"""Explanatory analysis section: MANOVA, ANOVAs, Hotelling and PCA."""

from saber11.core.formatting.spanish_numbers import fmt_num, fmt_p, fmt_p_clause
from saber11.models.dataset.dataset_models import SCORE_LABELS, SCORES, SHIFT_LABELS
from saber11.models.report.report_models import PipelineResults
from saber11.renderers.report.pdf_sections_sensitivity import sensitivity_block
from saber11.renderers.report.pdf_styles import H1, H2, make_table, para


def _manova_rows(results: PipelineResults) -> list[list[str]]:
    rows = [["Estadístico", "Valor", "F", "gl num", "gl den", "p"]]
    for t in results.manova.tests:
        rows.append([t.name, fmt_num(t.value), fmt_num(t.f_value, 2), fmt_num(t.df_num, 0),
                     fmt_num(t.df_den, 0), fmt_p(t.p_value)])
    return rows


def _anova_rows(results: PipelineResults) -> list[list[str]]:
    rows = [["Prueba", "F", "p", "p Bonferroni", "η²", "Decisión"]]
    for a in results.manova.anovas:
        dec = "Significativa" if a.p_bonferroni < results.metadata.alpha else "No significativa"
        rows.append([SCORE_LABELS[a.score], fmt_num(a.f_value, 2), fmt_p(a.p_value),
                     fmt_p(a.p_bonferroni), fmt_num(a.eta_squared), dec])
    return rows


def _hotelling_rows(results: PipelineResults) -> list[list[str]]:
    rows = [["Par", "T²", "F", "p", "p Bonferroni", "Decisión"]]
    for p in results.hotelling:
        dec = "Difieren" if p.p_bonferroni < results.metadata.alpha else "No difieren"
        rows.append([f"{SHIFT_LABELS.get(p.group_a, p.group_a)} vs {SHIFT_LABELS.get(p.group_b, p.group_b)}",
                     fmt_num(p.t2, 2), fmt_num(p.f_value, 2), fmt_p(p.p_value), fmt_p(p.p_bonferroni), dec])
    return rows


def _pca_rows(results: PipelineResults) -> tuple[list, list]:
    pca = results.pca
    cum = 0.0
    eig = [["Componente", "Autovalor", "% varianza", "% acumulado"]]
    for i, (v, r) in enumerate(zip(pca.eigenvalues, pca.explained_ratio), 1):
        cum += r
        eig.append([f"CP{i}", fmt_num(v), fmt_num(r * 100, 1), fmt_num(cum * 100, 1)])
    cols = list(pca.loadings.columns)
    load = [["Prueba", *[c.replace("PC", "CP") for c in cols]]]
    for s in SCORES:
        load.append([SCORE_LABELS[s], *[fmt_num(pca.loadings.loc[s, c]) for c in cols]])
    return eig, load


def explanatory_section(results: PipelineResults) -> list:
    """Build section 5."""
    m, pca = results.manova, results.pca
    eig, load = _pca_rows(results)
    cp1 = [["Jornada", "Media CP1"]] + [[SHIFT_LABELS.get(g, g), fmt_num(v)] for g, v in pca.cp1_means.items()]
    return [para("5. Análisis explicativo", H1), para("MANOVA", H2), make_table(_manova_rows(results)),
            para(f"η² parcial (Pillai) = {fmt_num(m.partial_eta_squared)}."),
            para("ANOVA por prueba (Bonferroni)", H2), make_table(_anova_rows(results)),
            para("T² de Hotelling por pares (Bonferroni)", H2), make_table(_hotelling_rows(results)),
            para("Componentes principales", H2), make_table(eig),
            para("Cargas", H2), make_table(load),
            para("Medias del CP1 por jornada", H2), make_table(cp1),
            para(f"ANOVA del CP1: F = {fmt_num(pca.cp1_f, 2)}, {fmt_p_clause(pca.cp1_p)}, "
                 f"η² = {fmt_num(pca.cp1_eta_squared)}."),
            *sensitivity_block(results)]

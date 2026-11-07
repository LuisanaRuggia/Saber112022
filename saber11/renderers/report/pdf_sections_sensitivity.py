"""Sensitivity subsection: MANOVA without outliers and within public schools only."""

from saber11.core.formatting.spanish_numbers import fmt_num, fmt_p, fmt_pct
from saber11.models.analysis.analysis_models import ManovaResult
from saber11.models.dataset.dataset_models import SCORE_SHORT_LABELS, SCORES, SHIFT_LABELS
from saber11.models.report.report_models import PipelineResults
from saber11.renderers.report.pdf_styles import H2, make_table, para


def _pillai_row(label: str, n: int, manova: ManovaResult) -> list[str]:
    return [label, fmt_num(n, 0), fmt_num(manova.pillai), fmt_p(manova.pillai_p), fmt_num(manova.partial_eta_squared)]


def _manova_rows(results: PipelineResults) -> list[list[str]]:
    sens, n_main = results.sensitivity, sum(results.descriptive.n_by_group.values())
    outliers = sens.without_outliers
    rows = [["Análisis", "n", "Pillai", "p", "η² parcial"], _pillai_row("Principal", n_main, results.manova),
            _pillai_row(f"Sin {outliers.n_removed} atípicos (intra-jornada)", n_main - outliers.n_removed,
                        outliers.manova)]
    official = sens.official_only
    if official.manova is not None:
        rows.append(_pillai_row("Solo colegios oficiales", official.n_sample, official.manova))
    return rows


def _profile_rows(results: PipelineResults) -> list[list[str]]:
    profile = results.sensitivity.official_only.profile
    rows = [["Jornada", "n", "Oficiales", "Privados", "% privados"]]
    for shift, r in profile.iterrows():
        share = "-" if r["share_private"] != r["share_private"] else fmt_pct(r["share_private"])
        rows.append([SHIFT_LABELS.get(shift, shift), fmt_num(r["n"], 0), fmt_num(r["n_official"], 0),
                     fmt_num(r["n_private"], 0), share])
    return rows


def _means_rows(results: PipelineResults) -> list[list[str]]:
    means = results.sensitivity.official_only.means
    rows = [["Naturaleza", "Jornada", "n", *[SCORE_SHORT_LABELS[s] for s in SCORES]]]
    for (nature, shift), r in means.iterrows():
        rows.append([nature.capitalize(), SHIFT_LABELS.get(shift, shift), fmt_num(r["n"], 0),
                     *[fmt_num(r[s], 1) for s in SCORES]])
    return rows


def _official_hotelling_rows(results: PipelineResults) -> list[list[str]]:
    rows = [["Par (solo oficiales)", "F", "p Bonferroni", "Decisión"]]
    for p in results.sensitivity.official_only.hotelling:
        dec = "Difieren" if p.p_bonferroni < results.metadata.alpha else "No difieren"
        rows.append([f"{SHIFT_LABELS.get(p.group_a, p.group_a)} vs {SHIFT_LABELS.get(p.group_b, p.group_b)}",
                     fmt_num(p.f_value, 2), fmt_p(p.p_bonferroni), dec])
    return rows


def sensitivity_block(results: PipelineResults) -> list:
    """Build the sensitivity subsections of section 5."""
    intro = ("En Bogotá la jornada está muy ligada a la naturaleza del colegio. Para separar ambos efectos se "
             "repite el MANOVA con una muestra estratificada por jornada solo de colegios oficiales; también se "
             "repite sin los atípicos detectados con la covarianza dentro de jornadas.")
    out = [para("Análisis de sensibilidad", H2), para(intro), make_table(_manova_rows(results)),
           para("Naturaleza del colegio por jornada (población de Bogotá)", H2), make_table(_profile_rows(results)),
           para("Medias por naturaleza y jornada (población de Bogotá)", H2), make_table(_means_rows(results))]
    if results.sensitivity.official_only.hotelling:
        out += [para("T² de Hotelling por pares, solo colegios oficiales", H2),
                make_table(_official_hotelling_rows(results))]
    return out

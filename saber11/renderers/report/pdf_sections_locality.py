"""Locality comparison block: normality check and the test it selects."""

from saber11.core.formatting.spanish_numbers import fmt_num, fmt_p
from saber11.models.dataset.dataset_models import SCORE_LABELS
from saber11.models.spatial.spatial_models import LocalityTestResult
from saber11.renderers.report.pdf_styles import H2, make_table, para

AVG_LABEL = "Promedio 5 pruebas"


def variable_label(variable: str) -> str:
    """Return the Spanish label of a compared variable."""
    return AVG_LABEL if variable == "avg_5" else SCORE_LABELS[variable]


def _method_text(tests: LocalityTestResult) -> str:
    excluded = f" Se excluyen por tamaño: {', '.join(tests.excluded)}." if tests.excluded else ""
    return (f"Muestra estratificada de hasta {tests.per_group} estudiantes por localidad (semilla {tests.seed}; "
            f"n = {fmt_num(tests.n_sample, 0)}, {tests.n_groups} localidades).{excluded} Para cada variable se "
            "aplica Shapiro-Wilk en cada localidad con corrección de Bonferroni entre localidades. Si ninguna "
            "rechaza la normalidad se usa ANOVA de una vía (η²); si alguna la rechaza se usa Kruskal-Wallis (ε²). "
            "Levene se reporta como referencia. El p ajustado aplica Bonferroni entre las variables comparadas.")


def _rows(tests: LocalityTestResult) -> list[list[str]]:
    rows = [["Variable", "Normalidad", "Levene p", "Prueba", "Estadístico", "p ajustado", "Efecto", "Decisión"]]
    for r in tests.rows:
        normality = "Cumple" if r.normal else f"No cumple ({r.n_rejected_normality})"
        decision = "Difieren" if r.p_bonferroni < 0.05 else "No difieren"
        rows.append([variable_label(r.variable), normality, fmt_p(r.levene_p), r.test,
                     fmt_num(r.statistic, 2), fmt_p(r.p_bonferroni),
                     f"{r.effect_label} = {fmt_num(r.effect_size, 3)}", decision])
    return rows


def locality_tests_block(tests: LocalityTestResult | None) -> list:
    """Build the locality comparison subsection, or a note when it could not run."""
    title = para("Comparación entre localidades", H2)
    if tests is None:
        return [title, para("No hay suficientes localidades con datos para comparar.")]
    note = para("Normalidad: entre paréntesis, número de localidades que rechazan Shapiro-Wilk.")
    return [title, para(_method_text(tests)), make_table(_rows(tests)), note]

"""Findings of the sensitivity analyses and the caveats of the study."""

from pathlib import PurePosixPath

from saber11.core.formatting.spanish_numbers import fmt_num, fmt_pct
from saber11.models.analysis.analysis_models import AssumptionsResult, MardiaResult
from saber11.models.analysis.sensitivity_models import NatureSensitivity, SensitivityResult
from saber11.models.spatial.spatial_models import SpatialResult
from saber11.services.conclusions.conclusions_text import differing_pairs, manova_clause, p_text, shift_label


def private_share_text(nature: NatureSensitivity) -> str:
    """Return 'Completa (x %), Mañana (y %), ...' with the private-school share of each shift."""
    shares = nature.profile["share_private"].dropna()
    return ", ".join(f"{shift_label(s)} ({fmt_pct(v)})" for s, v in shares.items())


def nature_findings(nature: NatureSensitivity, alpha: float) -> list[str]:
    """Describe how shift and school nature overlap, and the public-schools-only MANOVA."""
    out = [f"La jornada se cruza con la naturaleza del colegio. Porcentaje de estudiantes de colegios "
           f"privados en la población: {private_share_text(nature)}."]
    if nature.manova is None:
        return out + ["No hay suficientes estudiantes de colegios oficiales en al menos dos jornadas "
                      "para repetir el MANOVA solo con ellos."]
    verb = "rechaza" if nature.manova.pillai_p < alpha else "no rechaza"
    sizes = nature.profile["n_official"]
    shifts = ", ".join(f"{shift_label(s)} {fmt_num(sizes[s], 0)}" for s in nature.official_shifts)
    out.append(f"Solo con colegios oficiales (estudiantes oficiales en la población: {shifts}; muestra de "
               f"{fmt_num(nature.n_sample, 0)}), el MANOVA "
               f"{verb} la igualdad de medias entre jornadas {manova_clause(nature.manova)}.")
    pairs = differing_pairs(nature.hotelling, alpha)
    out.append("Entre colegios oficiales difieren los pares: " + "; ".join(pairs) + "." if pairs
               else "Entre colegios oficiales ningún par de jornadas difiere según T² de Hotelling con Bonferroni.")
    return out


def outlier_finding(sensitivity: SensitivityResult, main_rejects: bool, alpha: float) -> str:
    """Say whether the MANOVA decision survives removing the within-shift outliers."""
    check = sensitivity.without_outliers
    rejects = check.manova.pillai_p < alpha
    verdict = "se mantiene" if rejects == main_rejects else "cambia"
    return (f"Sin los {check.n_removed} atípicos detectados dentro de cada jornada, la decisión del MANOVA "
            f"{verdict} {manova_clause(check.manova)}.")


def _mardia_text(mardia: MardiaResult, alpha: float) -> str:
    verb = "rechaza" if min(mardia.skewness_p, mardia.kurtosis_p) < alpha else "no rechaza"
    return f"{verb} (asimetría p {p_text(mardia.skewness_p)}, curtosis p {p_text(mardia.kurtosis_p)})"


def assumption_caveats(assump: AssumptionsResult, alpha: float, n_sample: int) -> list[str]:
    """Return the caveats about normality, covariances and outliers."""
    box, guide, within = assump.box_m, assump.mahalanobis, assump.mahalanobis_within
    return [
        f"Mardia, calculado como en la guía, {_mardia_text(assump.mardia, alpha)}; sobre los residuos dentro "
        f"de cada jornada, que es el supuesto del MANOVA, {_mardia_text(assump.mardia_within, alpha)}. "
        "Con grupos balanceados el MANOVA con Pillai es robusto a esta violación.",
        f"La prueba M de Box {'rechaza' if box.p_value < alpha else 'no rechaza'} la igualdad de covarianzas "
        f"(p {p_text(box.p_value)}).",
        f"Hay {guide.n_outliers} atípicos multivariados con el método de la guía ({fmt_pct(guide.pct_outliers / 100)} "
        f"de la muestra) y {within.n_outliers} con la covarianza dentro de jornadas "
        f"({fmt_pct(within.n_outliers / n_sample)}).",
    ]


def design_caveats(spatial: SpatialResult, period: str, n_sample: int, n_pop: int) -> list[str]:
    """Return the caveats about the design, the data and the school directory."""
    out = [
        "El diseño es observacional: los resultados muestran asociación, no causa. La jornada se asocia con la "
        "naturaleza del colegio y con el nivel socioeconómico; el análisis solo con colegios oficiales controla "
        "lo primero, no lo segundo.",
        f"Los análisis inferenciales usan una muestra de {fmt_num(n_sample, 0)} estudiantes; las medias de la "
        f"población ({fmt_num(n_pop, 0)} estudiantes, uno por registro único) son descriptivas.",
    ]
    loc = spatial.localities
    if loc is not None:
        name = PurePosixPath(loc.directory_source).name or loc.directory_source
        out.append(f"Las localidades se asignan con el directorio de colegios vigente ({name}), no con el del "
                   f"periodo {period}: colegios cerrados o trasladados desde entonces pueden quedar sin localidad o "
                   f"con otra ({fmt_pct(1 - loc.match_rate)} de los estudiantes no se pudo cruzar).")
    return out

"""Narrative conclusions in Spanish, derived only from the analysis results."""

from saber11.core.formatting.spanish_numbers import fmt_num, fmt_p_clause, fmt_pct
from saber11.models.analysis.analysis_models import (
    AssumptionsResult, DescriptiveResult, HotellingPair, ManovaResult, PcaResult)
from saber11.models.analysis.sensitivity_models import SensitivityResult
from saber11.models.dataset.dataset_models import SCORE_LABELS
from saber11.models.report.report_models import Conclusions
from saber11.models.spatial.spatial_models import SpatialResult
from saber11.services.conclusions.conclusions_sensitivity import (
    assumption_caveats, design_caveats, nature_findings, outlier_finding)
from saber11.services.conclusions.conclusions_text import (
    differing_pairs, manova_clause, p_text, shift_label)

_REASONS = {"ANOVA": "se cumplen la normalidad y la igualdad de varianzas",
            "ANOVA de Welch": "se cumple la normalidad pero no la igualdad de varianzas",
            "Kruskal-Wallis": "no se cumple la normalidad"}


def _manova_finding(manova: ManovaResult, alpha: float) -> str:
    rejects = manova.pillai_p < alpha
    verb = "rechaza" if rejects else "no rechaza"
    tail = ("hay diferencias en el vector de medias entre jornadas." if rejects
            else "no hay evidencia de diferencias en el vector de medias entre jornadas.")
    return f"El MANOVA {verb} la igualdad de vectores de medias entre jornadas {manova_clause(manova)}: {tail}"


def _anova_finding(manova: ManovaResult, alpha: float) -> str:
    sig = [SCORE_LABELS[a.score] for a in manova.anovas if a.p_bonferroni < alpha]
    if not sig:
        return ("Ninguna de las cinco pruebas muestra diferencias significativas entre jornadas "
                "tras la corrección de Bonferroni.")
    return ("Tras la corrección de Bonferroni, los ANOVA son significativos en: "
            + ", ".join(sig) + f" ({len(sig)} de {len(manova.anovas)}).")


def _hotelling_findings(pairs: list[HotellingPair], alpha: float) -> list[str]:
    diff = differing_pairs(pairs, alpha)
    same = [f"{shift_label(p.group_a)} y {shift_label(p.group_b)}" for p in pairs if p.p_bonferroni >= alpha]
    if not diff:
        return ["Según T² de Hotelling con Bonferroni, ningún par de jornadas difiere."]
    out = ["Según T² de Hotelling con Bonferroni, difieren los pares: " + "; ".join(diff) + "."]
    if same:
        out.append("No difieren los pares: " + "; ".join(same) + ".")
    return out


def _gap_finding(desc: DescriptiveResult) -> str:
    gaps = desc.means.max() - desc.means.min()
    score = gaps.idxmax()
    best, worst = desc.means[score].idxmax(), desc.means[score].idxmin()
    return (f"La mayor brecha entre jornadas está en {SCORE_LABELS[score]}: {shift_label(best)} "
            f"({fmt_num(desc.means.loc[best, score], 1)} puntos) frente a {shift_label(worst)} "
            f"({fmt_num(desc.means.loc[worst, score], 1)} puntos), una diferencia de {fmt_num(gaps[score], 1)} puntos.")


def _pca_findings(pca: PcaResult) -> list[str]:
    load = pca.loadings["PC1"]
    same_sign = bool((load > 0).all() or (load < 0).all())
    similar = float(load.abs().max() - load.abs().min()) < 0.3
    lo, hi = fmt_num(float(load.abs().min()), 2), fmt_num(float(load.abs().max()), 2)
    text = f"El primer componente explica {fmt_pct(pca.explained_ratio[0])} de la varianza"
    if same_sign and similar:
        text += (f"; todas las cargas tienen el mismo signo y valores entre {lo} y {hi}, "
                 "por lo que se interpreta como un factor general de desempeño.")
    else:
        text += "; sus cargas no son homogéneas, así que no se interpreta como un factor general."
    order = sorted(pca.cp1_means.items(), key=lambda kv: kv[1], reverse=True)
    rank = ", ".join(f"{shift_label(k)} ({fmt_num(v, 2)})" for k, v in order)
    return [text, f"Ranking de jornadas por media del CP1: {rank} (ANOVA del CP1: p {p_text(pca.cp1_p)})."]


def _department_finding(spatial: SpatialResult) -> str:
    d = spatial.departments
    if d.bogota_rank is None:
        return "Bogotá no aparece en el ranking de departamentos."
    return (f"Bogotá ocupa el puesto {d.bogota_rank} de {d.n_departments} departamentos "
            "en Matemáticas más Lectura Crítica.")


def _locality_finding(spatial: SpatialResult) -> str:
    loc = spatial.localities
    if loc is None or loc.table.empty:
        return "No se pudo cruzar la información por localidad con el directorio de colegios."
    t = loc.table.sort_values("avg_5", ascending=False)
    best, worst = t.iloc[0], t.iloc[-1]
    return (f"Por localidad, el promedio más alto es el de {best['localidad']} ({fmt_num(best['avg_5'], 1)} puntos) y "
            f"el más bajo el de {worst['localidad']} ({fmt_num(worst['avg_5'], 1)}); el cruce con el directorio cubre "
            f"{fmt_pct(loc.match_rate)} de los estudiantes.")


def _locality_test_finding(spatial: SpatialResult) -> list[str]:
    tests = spatial.localities.tests if spatial.localities else None
    if tests is None:
        return []
    labels = {"avg_5": "el promedio de las 5 pruebas", **SCORE_LABELS}
    differ = [labels[r.variable] for r in tests.rows if r.p_bonferroni < tests.alpha]
    main = tests.rows[0]
    verb = "difiere" if main.p_bonferroni < tests.alpha else "no difiere"
    head = (f"Entre localidades, {labels[main.variable]} {verb} ({main.test}, porque {_REASONS[main.test]}; "
            f"{fmt_p_clause(main.p_bonferroni).replace('p ', 'p ajustado ', 1)}, "
            f"{main.effect_label} = {fmt_num(main.effect_size, 3)}).")
    detail = (f"Las localidades difieren en: {', '.join(differ)}." if differ
              else "Ninguna prueba muestra diferencias entre localidades tras Bonferroni.")
    return [head, detail]


def _headline(manova: ManovaResult, sensitivity: SensitivityResult, alpha: float) -> str:
    if manova.pillai_p >= alpha:
        return "No hay evidencia de diferencias en el rendimiento de Saber 11 entre jornadas en Bogotá."
    official = sensitivity.official_only.manova
    if official is None:
        return "Las jornadas escolares se asocian con diferencias en el rendimiento de Saber 11 en Bogotá."
    if official.pillai_p < alpha:
        return ("Las jornadas escolares se asocian con diferencias en el rendimiento de Saber 11 en Bogotá, "
                "también al comparar solo colegios oficiales.")
    share = sensitivity.official_only.profile.loc["COMPLETA", "share_private"]
    return ("Las diferencias entre jornadas en Bogotá desaparecen al comparar solo colegios oficiales: "
            f"la jornada Completa reúne sobre todo colegios privados ({fmt_pct(share)} de sus estudiantes).")


def draw_conclusions(descriptive: DescriptiveResult, assumptions: AssumptionsResult, manova: ManovaResult,
                     hotelling: list[HotellingPair], pca: PcaResult, spatial: SpatialResult,
                     sensitivity: SensitivityResult, alpha: float, period: str) -> Conclusions:
    """Build the headline, findings and caveats from the results."""
    findings = [_manova_finding(manova, alpha), _anova_finding(manova, alpha),
                *_hotelling_findings(hotelling, alpha), _gap_finding(descriptive),
                *nature_findings(sensitivity.official_only, alpha),
                outlier_finding(sensitivity, manova.pillai_p < alpha, alpha),
                *_pca_findings(pca), _department_finding(spatial), _locality_finding(spatial),
                *_locality_test_finding(spatial)]
    n_sample = sum(descriptive.n_by_group.values())
    n_pop = sum(descriptive.population_n_by_group.values())
    caveats = [*assumption_caveats(assumptions, alpha, n_sample), *design_caveats(spatial, period, n_sample, n_pop)]
    return Conclusions(_headline(manova, sensitivity, alpha), findings, caveats)

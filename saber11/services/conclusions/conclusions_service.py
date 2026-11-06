"""Narrative conclusions in Spanish, derived only from the analysis results."""

from saber11.core.formatting.spanish_numbers import fmt_num, fmt_p, fmt_pct
from saber11.models.analysis.analysis_models import (
    AssumptionsResult, DescriptiveResult, HotellingPair, ManovaResult, PcaResult)
from saber11.models.dataset.dataset_models import SCORE_LABELS, SHIFT_LABELS
from saber11.models.report.report_models import Conclusions
from saber11.models.spatial.spatial_models import SpatialResult


def _shift(code: str) -> str:
    return SHIFT_LABELS.get(code, code)


def _manova_finding(manova: ManovaResult, alpha: float) -> str:
    rejects = manova.pillai_p < alpha
    verb = "rechaza" if rejects else "no rechaza"
    tail = ("hay diferencias en el vector de medias entre jornadas." if rejects
            else "no hay evidencia de diferencias en el vector de medias entre jornadas.")
    return (f"El MANOVA {verb} la igualdad de vectores de medias entre jornadas "
            f"(Pillai = {fmt_num(manova.pillai)}, p {_p_text(manova.pillai_p)}, "
            f"η² parcial = {fmt_num(manova.partial_eta_squared)}): {tail}")


def _p_text(p: float) -> str:
    return fmt_p(p) if p < 0.001 else "= " + fmt_p(p)


def _anova_finding(manova: ManovaResult, alpha: float) -> str:
    sig = [SCORE_LABELS[a.score] for a in manova.anovas if a.p_bonferroni < alpha]
    if not sig:
        return "Ninguna de las cinco pruebas muestra diferencias significativas entre jornadas tras la corrección de Bonferroni."
    return ("Tras la corrección de Bonferroni, los ANOVA son significativos en: "
            + ", ".join(sig) + f" ({len(sig)} de {len(manova.anovas)}).")


def _hotelling_findings(pairs: list[HotellingPair], alpha: float) -> list[str]:
    diff = [f"{_shift(p.group_a)} y {_shift(p.group_b)} (p ajustado {_p_text(p.p_bonferroni)})"
            for p in pairs if p.p_bonferroni < alpha]
    same = [f"{_shift(p.group_a)} y {_shift(p.group_b)}" for p in pairs if p.p_bonferroni >= alpha]
    out = []
    if diff:
        out.append("Según T² de Hotelling con Bonferroni, difieren los pares: " + "; ".join(diff) + ".")
    else:
        out.append("Según T² de Hotelling con Bonferroni, ningún par de jornadas difiere.")
    if same and diff:
        out.append("No difieren los pares: " + "; ".join(same) + ".")
    return out


def _gap_finding(desc: DescriptiveResult) -> str:
    gaps = desc.means.max() - desc.means.min()
    score = gaps.idxmax()
    best, worst = desc.means[score].idxmax(), desc.means[score].idxmin()
    return (f"La mayor brecha entre jornadas está en {SCORE_LABELS[score]}: {_shift(best)} "
            f"({fmt_num(desc.means.loc[best, score], 1)} puntos) frente a {_shift(worst)} "
            f"({fmt_num(desc.means.loc[worst, score], 1)} puntos), una diferencia de {fmt_num(gaps[score], 1)} puntos.")


def _pca_findings(pca: PcaResult) -> list[str]:
    load = pca.loadings["PC1"]
    share = fmt_pct(pca.explained_ratio[0])
    same_sign = bool((load > 0).all() or (load < 0).all())
    similar = float(load.abs().max() - load.abs().min()) < 0.3
    lo, hi = fmt_num(float(load.abs().min()), 2), fmt_num(float(load.abs().max()), 2)
    text = f"El primer componente explica {share} de la varianza"
    if same_sign and similar:
        text += (f"; todas las cargas tienen el mismo signo y valores entre {lo} y {hi}, "
                 "por lo que se interpreta como un factor general de desempeño.")
    else:
        text += "; sus cargas no son homogéneas, así que no se interpreta como un factor general."
    order = sorted(pca.cp1_means.items(), key=lambda kv: kv[1], reverse=True)
    rank = ", ".join(f"{_shift(k)} ({fmt_num(v, 2)})" for k, v in order)
    return [text, f"Ranking de jornadas por media del CP1: {rank} (ANOVA del CP1: p {_p_text(pca.cp1_p)})."]


def _department_finding(spatial: SpatialResult) -> str:
    d = spatial.departments
    if d.bogota_rank is None:
        return "Bogotá no aparece en el ranking de departamentos."
    return f"Bogotá ocupa el puesto {d.bogota_rank} de {d.n_departments} departamentos en Matemáticas más Lectura Crítica."


def _locality_finding(spatial: SpatialResult) -> str:
    loc = spatial.localities
    if loc is None or loc.table.empty:
        return "No se pudo cruzar la información por localidad con el directorio de colegios."
    t = loc.table.sort_values("avg_5", ascending=False)
    best, worst = t.iloc[0], t.iloc[-1]
    return (f"Por localidad, la mejor es {best['localidad']} ({fmt_num(best['avg_5'], 1)} puntos) y la peor "
            f"{worst['localidad']} ({fmt_num(worst['avg_5'], 1)}); el cruce con el directorio cubre "
            f"{fmt_pct(loc.match_rate)} de los estudiantes.")


def _caveats(assump: AssumptionsResult, alpha: float, n_sample: int, n_pop: int) -> list[str]:
    mardia = assump.mardia
    rejected = min(mardia.skewness_p, mardia.kurtosis_p) < alpha
    box = assump.box_m
    return [
        ("Mardia rechaza la normalidad multivariada" if rejected else "Mardia no rechaza la normalidad multivariada")
        + f" (asimetría p {_p_text(mardia.skewness_p)}, curtosis p {_p_text(mardia.kurtosis_p)}); "
        "con grupos balanceados el MANOVA con Pillai es robusto a esta violación.",
        f"La prueba M de Box {'rechaza' if box.p_value < alpha else 'no rechaza'} la igualdad de covarianzas "
        f"(p {_p_text(box.p_value)}).",
        f"Hay {assump.mahalanobis.n_outliers} atípicos multivariados ({fmt_pct(assump.mahalanobis.pct_outliers / 100)} de la muestra).",
        "El diseño es observacional: los resultados muestran asociación, no causa.",
        f"Los análisis inferenciales usan una muestra de {fmt_num(n_sample, 0)} estudiantes; las medias de la población "
        f"({fmt_num(n_pop, 0)} estudiantes) son descriptivas.",
    ]


def draw_conclusions(descriptive, assumptions, manova, hotelling, pca, spatial, alpha) -> Conclusions:
    """Build the headline, findings and caveats from the results."""
    rejects = manova.pillai_p < alpha
    headline = ("Las jornadas escolares se asocian con diferencias en el rendimiento de Saber 11 en Bogotá."
                if rejects else "No hay evidencia de diferencias en el rendimiento de Saber 11 entre jornadas en Bogotá.")
    findings = [_manova_finding(manova, alpha), _anova_finding(manova, alpha),
                *_hotelling_findings(hotelling, alpha), _gap_finding(descriptive),
                *_pca_findings(pca), _department_finding(spatial), _locality_finding(spatial)]
    n_sample = sum(descriptive.n_by_group.values())
    n_pop = sum(descriptive.population_n_by_group.values())
    return Conclusions(headline, findings, _caveats(assumptions, alpha, n_sample, n_pop))

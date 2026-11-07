"""Cover, executive summary and a brief data-and-method section."""

from reportlab.platypus import PageBreak, Spacer

from saber11.core.formatting.spanish_numbers import fmt_num, fmt_p_clause
from saber11.models.report.report_models import PipelineResults
from saber11.renderers.report.pdf_styles import H1, H2, SUBTITLE, TITLE, bullet, para


def cover(results: PipelineResults) -> list:
    """Build the cover page: title, period, source and date only."""
    m = results.metadata
    return [Spacer(1, 160), para("Saber 11 Bogotá: rendimiento por jornada", TITLE),
            para("Resumen de resultados", SUBTITLE), Spacer(1, 24),
            para(f"Periodo: {m.period}", SUBTITLE), para(f"Fuente: {m.source_detail}", SUBTITLE),
            para(f"Fecha de generación: {m.generated_at}", SUBTITLE), PageBreak()]


def summary(results: PipelineResults) -> list:
    """Build section 1."""
    r = results
    official = r.sensitivity.official_only.manova
    key = [f"MANOVA: Pillai = {fmt_num(r.manova.pillai)}, {fmt_p_clause(r.manova.pillai_p)}, "
           f"η² parcial = {fmt_num(r.manova.partial_eta_squared)}.",
           f"El primer componente principal explica {fmt_num(r.pca.explained_ratio[0] * 100, 1)} % de la varianza.",
           f"Población de Bogotá: {fmt_num(r.metadata.population_size, 0)} estudiantes; "
           f"muestra de {fmt_num(r.metadata.sample_per_group, 0)} por jornada."]
    if official is not None:
        key.append(f"Solo colegios oficiales: Pillai = {fmt_num(official.pillai)}, {fmt_p_clause(official.pillai_p)}.")
    return [para("1. Resumen ejecutivo", H1), para(f"<b>{r.conclusions.headline}</b>"),
            para("Cifras clave", H2), *[bullet(k) for k in key]]


def methodology(results: PipelineResults) -> list:
    """Build section 2: one paragraph on the data and one on the method."""
    m = results.metadata
    period = (" Es el periodo más reciente con microdatos por estudiante en datos abiertos; los de 2023 a 2025 "
              "solo se distribuyen por DataIcfes." if m.source == "api" else "")
    data = (f"Se usan los resultados del Saber 11 del periodo {m.period} ({m.source_detail}).{period} Se incluyen "
            "los estudiantes de colegios de Bogotá en las jornadas Completa, Mañana, Tarde y Única, con los cinco "
            "puntajes completos y un registro por estudiante, porque la fuente repite filas.")
    method = (f"Sobre una muestra estratificada de {m.sample_per_group} estudiantes por jornada (semilla {m.seed}) "
              "se revisan los supuestos (Mahalanobis, Mardia y M de Box), se aplica un MANOVA "
              "con T² de Hotelling por pares (Bonferroni), y un análisis de componentes principales. Se completa con "
              "un análisis espacial por departamento y localidad, y con dos análisis de sensibilidad: sin atípicos y "
              f"solo con colegios oficiales. Nivel de significancia: α = {fmt_num(m.alpha, 2)}.")
    return [para("2. Datos y método", H1), para(data), para(method)]

"""Cover, executive summary and methodology sections."""

from reportlab.platypus import PageBreak, Spacer

from saber11.core.formatting.spanish_numbers import fmt_num, fmt_p, fmt_p_clause
from saber11.models.report.report_models import PipelineResults
from saber11.renderers.report.pdf_styles import H1, H2, TITLE, bullet, para

TEAM = ("Juan Sebastián Rueda", "David Florez", "Luisana Gutiérrez Ruggia")


def cover(results: PipelineResults) -> list:
    """Build the cover page."""
    m = results.metadata
    items = [Spacer(1, 120), para("Saber 11 Bogotá: rendimiento por jornada", TITLE),
             para(f"Periodo: {m.period}"), para(f"Fuente: {m.source_detail}"),
             para(f"Fecha de generación: {m.generated_at}"), Spacer(1, 24), para("<b>Integrantes</b>")]
    return [*items, *[para(name) for name in TEAM], PageBreak()]


def summary(results: PipelineResults) -> list:
    """Build section 1."""
    r = results
    key = [f"MANOVA: Pillai = {fmt_num(r.manova.pillai)}, {fmt_p_clause(r.manova.pillai_p)}, "
           f"η² parcial = {fmt_num(r.manova.partial_eta_squared)}.",
           f"CP1 explica {fmt_num(r.pca.explained_ratio[0] * 100, 1)} % de la varianza.",
           f"Población de Bogotá: {fmt_num(r.metadata.population_size, 0)} estudiantes; "
           f"muestra de {fmt_num(r.metadata.sample_per_group, 0)} por jornada."]
    return [para("1. Resumen ejecutivo", H1), para(f"<b>{r.conclusions.headline}</b>"),
            para("Cifras clave", H2), *[bullet(k) for k in key]]


def methodology(results: PipelineResults) -> list:
    """Build section 2."""
    m = results.metadata
    a = fmt_num(m.alpha, 2)
    sources = [f"Fuente de datos: {m.source_detail}.",
               "Filtros: colegios de Bogotá; jornadas Completa, Mañana, Tarde y Única "
               "(se excluyen Noche y Sabatina); sin puntajes faltantes.",
               "Registros repetidos: la fuente repite filas idénticas de un mismo estudiante; se conserva un "
               "registro por estudiante (estu_consecutivo). Los conteos de población son de estudiantes únicos."]
    if m.source == "api":
        sources.append("Periodo: es el periodo más reciente con microdatos por estudiante en datos abiertos "
                       "(datos.gov.co). Los periodos 2023 a 2025 solo se distribuyen por DataIcfes, con registro; "
                       "el pipeline puede procesarlos sin cambios en el código cuando se disponga del archivo.")
    design = [f"Muestra estratificada por jornada: {m.sample_per_group} estudiantes por grupo, semilla {m.seed}."]
    tests = ["Estadística descriptiva (medias, desviaciones, covarianzas, correlaciones).",
             "Distancia de Mahalanobis (atípicos), normalidad multivariada de Mardia y M de Box; Mahalanobis y "
             "Mardia se calculan como en la guía y también sobre los residuos dentro de cada jornada.",
             f"MANOVA (Pillai, Wilks, Hotelling-Lawley, Roy) con α = {a}.",
             "ANOVA por prueba y T² de Hotelling por pares, con corrección de Bonferroni "
             f"(α dividido por el número de comparaciones; α global = {a}).",
             "Análisis de componentes principales sobre la matriz de correlación y ANOVA del CP1.",
             "Sensibilidad: MANOVA sin los atípicos intra-jornada y MANOVA y T² de Hotelling solo con colegios "
             "oficiales, para separar la jornada de la naturaleza del colegio.",
             "Ranking de departamentos y resultados por localidad (Shapiro-Wilk; ANOVA, ANOVA de Welch o "
             "Kruskal-Wallis según los supuestos)."]
    return [para("2. Datos y metodología", H1), para("Fuentes y filtros", H2), *[bullet(s) for s in sources],
            para("Diseño de la muestra", H2), *[bullet(s) for s in design],
            para("Pruebas aplicadas", H2), *[bullet(s) for s in tests]]

"""Spatial, conclusions and sources sections."""

from saber11.core.formatting.spanish_numbers import fmt_num, fmt_pct
from saber11.models.dataset.dataset_models import SCORE_LABELS, SCORE_SHORT_LABELS, SCORES
from saber11.models.report.report_models import PipelineResults
from saber11.renderers.report.pdf_sections_locality import locality_tests_block
from saber11.renderers.charts.result_charts import locality_chart
from saber11.renderers.report.pdf_styles import H1, H2, bullet, figure, make_table, para

def _department_rows(results: PipelineResults) -> tuple[list, tuple[int, ...]]:
    table = results.spatial.departments.table.sort_values("rank").head(33)
    rows = [["Puesto", "Departamento", "n", *[SCORE_SHORT_LABELS[s] for s in SCORES], "Mat.+Lect.", "Prom. 5"]]
    bold = []
    for i, (_, r) in enumerate(table.iterrows()):
        rows.append([fmt_num(r["rank"], 0), r["department"], fmt_num(r["n"], 0),
                     *[fmt_num(r[s], 1) for s in SCORES], fmt_num(r["math_reading"], 1), fmt_num(r["avg_5"], 1)])
        if "BOGOT" in str(r["department"]).upper():
            bold.append(i)
    return rows, tuple(bold)


def _locality_block(results: PipelineResults) -> list:
    loc = results.spatial.localities
    if loc is None:
        return [para("No se pudo obtener el directorio de colegios, por lo que no hay resultados por localidad.")]
    rows = [["Localidad", "n", *[SCORE_SHORT_LABELS[s] for s in SCORES], "Prom. 5"]]
    for _, r in loc.table.iterrows():
        rows.append([r["localidad"], fmt_num(r["n"], 0), *[fmt_num(r[s], 1) for s in SCORES], fmt_num(r["avg_5"], 1)])
    chart = figure(locality_chart(loc.table), "Figura 7. Promedio de las cinco pruebas por localidad.", width=380)
    return [make_table(rows), chart, para(f"Tasa de cruce con el directorio: {fmt_pct(loc.match_rate)} "
                                   f"de {fmt_num(loc.n_students, 0)} estudiantes. Directorio: {loc.directory_source}"),
            *locality_tests_block(loc.tests)]


def spatial_section(results: PipelineResults) -> list:
    """Build section 6."""
    rows, bold = _department_rows(results)
    legend = " ".join(f"{SCORE_SHORT_LABELS[s]} = {SCORE_LABELS[s]}." for s in SCORES)
    note = ("Mismos filtros que la población de Bogotá: jornadas Completa, Mañana, Tarde y Única, sin puntajes "
            "faltantes y un registro por estudiante. Solo departamentos con 30 estudiantes o más.")
    return [para("6. Análisis espacial", H1), para("Ranking de departamentos", H2), make_table(rows, bold),
            para(legend), para(note), para("Resultados por localidad de Bogotá", H2), *_locality_block(results)]


def conclusions_section(results: PipelineResults) -> list:
    """Build section 7."""
    c = results.conclusions
    return [para("7. Conclusiones", H1), para(f"<b>{c.headline}</b>"), para("Hallazgos", H2),
            *[bullet(f) for f in c.findings], para("Limitaciones", H2), *[bullet(x) for x in c.caveats]]


def sources_section(results: PipelineResults) -> list:
    """Build section 8."""
    items = [results.metadata.source_detail,
             "Datos Abiertos Bogotá: directorio de colegios de la SED (GeoJSON).",
             "Datos Abiertos Colombia (datos.gov.co): Resultados Saber 11, Icfes.",
             "Icfes DataIcfes: microdatos Saber 11."]
    return [para("8. Fuentes", H1), *[bullet(i) for i in items]]

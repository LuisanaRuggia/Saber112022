from pypdf import PdfReader

from saber11.renderers.report.pdf_renderer import render_pdf
from tests.fakes.results_factory import build_results

SECTIONS = ("1. Resumen ejecutivo", "2. Datos y método", "3. Análisis descriptivo", "4. Supuestos",
            "5. Análisis explicativo", "6. Análisis espacial", "7. Conclusiones", "8. Fuentes")


def _text(path):
    return "\n".join(p.extract_text() for p in PdfReader(str(path)).pages)


def test_renders_valid_multipage_pdf(tmp_path):
    out = render_pdf(build_results(), tmp_path / "r.pdf")
    assert out.read_bytes().startswith(b"%PDF")
    assert len(PdfReader(str(out)).pages) > 1


def test_contains_sections_and_cover(tmp_path):
    text = _text(render_pdf(build_results(), tmp_path / "r.pdf"))
    for title in SECTIONS:
        assert title in text
    for name in ("David Florez", "Luisana", "Juan Sebastián", "Integrantes"):
        assert name not in text
    assert "0,202" in text and "Página" in text


def test_without_localities_shows_note(tmp_path):
    text = _text(render_pdf(build_results(with_localities=False), tmp_path / "r.pdf"))
    assert "no hay resultados por localidad" in text


def test_outlier_share_is_rendered_as_percentage_once(tmp_path):
    from pypdf import PdfReader
    from saber11.renderers.report.pdf_renderer import render_pdf
    from tests.fakes.results_factory import build_results

    text = "".join(p.extract_text() for p in PdfReader(render_pdf(build_results(), tmp_path / "r.pdf")).pages)
    assert "3,8 %" in text and "375,0 %" not in text and "p = <" not in text


def test_locality_comparison_table_is_rendered(tmp_path):
    from pypdf import PdfReader
    from saber11.renderers.report.pdf_renderer import render_pdf
    from tests.fakes.results_factory import build_results

    text = "".join(p.extract_text() for p in PdfReader(render_pdf(build_results(), tmp_path / "r.pdf")).pages)
    assert "Comparación entre localidades" in text and "Shapiro-Wilk" in text and "Kruskal-Wallis" in text


def test_api_source_explains_why_this_period(tmp_path):
    from dataclasses import replace
    from pypdf import PdfReader
    from saber11.renderers.report.pdf_renderer import render_pdf
    from tests.fakes.results_factory import build_results

    base = build_results()
    for source, expected in (("api", True), ("dataicfes", False)):
        r = replace(base, metadata=replace(base.metadata, source=source))
        text = " ".join(p.extract_text() for p in PdfReader(render_pdf(r, tmp_path / f"{source}.pdf")).pages)
        assert ("periodo más reciente con microdatos" in " ".join(text.split())) is expected


def test_sensitivity_and_within_shift_tables_are_rendered(tmp_path):
    text = " ".join(_text(render_pdf(build_results(), tmp_path / "r.pdf")).split())
    for expected in ("Análisis de sensibilidad", "Solo colegios oficiales", "% privados",
                     "Dentro de jornadas", "Mardia curtosis (residuos)", "un registro por estudiante",
                     "ANOVA de Welch", "Solo departamentos con 30 estudiantes o más"):
        assert expected in text


def test_report_has_figures_and_no_per_test_anova(tmp_path):
    reader = PdfReader(str(render_pdf(build_results(), tmp_path / "r.pdf")))
    images = sum(len(page.images) for page in reader.pages)
    text = " ".join(" ".join(p.extract_text() for p in reader.pages).split())
    assert images == 7
    for caption in ("Figura 1.", "Figura 3. Normalidad multivariada de Mardia", "Figura 7."):
        assert caption in text
    assert "ANOVA por prueba" not in text and "Matriz de correlaciones" in text


def test_report_uses_arial_compatible_font_and_no_colors(tmp_path):
    from saber11.renderers.report.pdf_fonts import FONTS
    from reportlab.lib import colors
    from saber11.renderers.report.pdf_styles import BODY, TABLE_STYLE

    assert FONTS.family in ("Arial", "Liberation Sans")
    assert BODY.alignment == 4  # TA_JUSTIFY
    assert not {c[0] for c in TABLE_STYLE} & {"BACKGROUND", "ROWBACKGROUNDS", "TEXTCOLOR"}
    assert all(c[4] == colors.black for c in TABLE_STYLE if len(c) > 4)
    reader = PdfReader(str(render_pdf(build_results(), tmp_path / "r.pdf")))
    fonts = {str(f["/BaseFont"]) for page in reader.pages for f in page["/Resources"].get("/Font", {}).values()
             if "/BaseFont" in f.get_object()}
    assert any("Arial" in f or "Liberation" in f for f in fonts)

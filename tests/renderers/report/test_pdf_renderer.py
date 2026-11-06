from pypdf import PdfReader

from saber11.renderers.report.pdf_renderer import render_pdf
from tests.fakes.results_factory import build_results

SECTIONS = ("1. Resumen ejecutivo", "2. Datos y metodología", "3. Análisis descriptivo", "4. Supuestos",
            "5. Análisis explicativo", "6. Análisis espacial", "7. Conclusiones", "8. Fuentes")


def _text(path):
    return "\n".join(p.extract_text() for p in PdfReader(str(path)).pages)


def test_renders_valid_multipage_pdf(tmp_path):
    out = render_pdf(build_results(), tmp_path / "r.pdf")
    assert out.read_bytes().startswith(b"%PDF")
    assert len(PdfReader(str(out)).pages) > 1


def test_contains_sections_and_cover(tmp_path):
    text = _text(render_pdf(build_results(), tmp_path / "r.pdf"))
    for title in (*SECTIONS, "David Florez", "Luisana"):
        assert title in text
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

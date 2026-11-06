from dataclasses import replace

from saber11.models.report.report_models import Conclusions
from tests.fakes.results_factory import build_results


def _text(c: Conclusions) -> str:
    return "\n".join([c.headline, *c.findings, *c.caveats])


def test_significant_scenario_reports_rejection_and_numbers():
    c = build_results(significant=True).conclusions
    text = _text(c)
    assert "0,202" in text and "0,067" in text and "< 0,001" in text
    assert "rechaza" in c.findings[0].lower()
    assert "Completa" in text and "diferencia" in text
    assert "76,5 %" in text and "factor general" in text
    assert "Bogotá" in text and "Chapinero" in text and "93,0 %" in text
    assert c.headline.count(".") == 1


def test_no_differences_scenario():
    c = build_results(significant=False).conclusions
    text = _text(c)
    assert "no rechaza" in c.findings[0].lower()
    assert "ningún par" in text.lower()


def test_caveats_cover_assumptions_and_design():
    caveats = " ".join(build_results().conclusions.caveats)
    for word in ("Mardia", "Box", "atípicos", "causa", "población"):
        assert word in caveats


def test_missing_localities_is_noted():
    c = build_results(with_localities=False).conclusions
    assert "localidad" in _text(c).lower() and "no se pudo" in _text(c).lower()


def test_no_em_dashes():
    assert "—" not in _text(build_results().conclusions)


def test_locality_comparison_names_the_test_used():
    from saber11.services.conclusions.conclusions_service import draw_conclusions

    r = build_results()
    c = draw_conclusions(r.descriptive, r.assumptions, r.manova, r.hotelling, r.pca, r.spatial, 0.05)
    text = " ".join(c.findings)
    assert "Kruskal-Wallis" in text and "promedio de las 5 pruebas" in text
    assert "p ajustado < 0,001" in text

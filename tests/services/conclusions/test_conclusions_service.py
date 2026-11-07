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
    c = draw_conclusions(r.descriptive, r.assumptions, r.manova, r.hotelling, r.pca, r.spatial, r.sensitivity,
                         0.05, "20224")
    text = " ".join(c.findings)
    assert "Kruskal-Wallis" in text and "promedio de las 5 pruebas" in text
    assert "p ajustado < 0,001" in text


def test_headline_flags_nature_confounding_when_public_schools_do_not_differ():
    c = build_results(significant=True, official_differs=False).conclusions
    assert "solo colegios oficiales" in c.headline and "98,0 %" in c.headline
    assert c.headline.count(".") == 1
    text = _text(c)
    assert "Solo con colegios oficiales" in text and "no rechaza" in text
    assert "Entre colegios oficiales ningún par" in text


def test_headline_when_public_schools_also_differ():
    c = build_results(significant=True, official_differs=True).conclusions
    assert "también al comparar solo colegios oficiales" in c.headline
    assert "Entre colegios oficiales difieren los pares" in _text(c)


def test_outlier_sensitivity_and_within_shift_checks_are_reported():
    text = _text(build_results().conclusions)
    assert "Sin los 12 atípicos" in text and "se mantiene" in text
    assert "residuos dentro de cada jornada" in text and "12 con la covarianza dentro de jornadas" in text


def test_directory_caveat_names_file_and_period():
    caveats = " ".join(build_results().conclusions.caveats)
    assert "dir.geojson" in caveats and "periodo 20224" in caveats and "7,0 %" in caveats


def test_locality_alpha_comes_from_the_tests():
    from dataclasses import replace
    from saber11.services.conclusions.conclusions_service import _locality_test_finding

    spatial = build_results().spatial
    strict = replace(spatial.localities.tests, alpha=1e-12)
    spatial = replace(spatial, localities=replace(spatial.localities, tests=strict))
    assert "Ninguna prueba muestra diferencias" in " ".join(_locality_test_finding(spatial))

import pandas as pd
import pytest

from saber11.core.errors.pipeline_errors import SourceUnavailableError
from saber11.models.dataset.dataset_models import SCORES
from saber11.services.spatial.spatial_service import build_spatial, locality_results, rank_departments


def departments():
    def row(name, n, math, reading):
        return {"department": name, "n": n, "punt_matematicas": math, "punt_lectura_critica": reading,
                "punt_c_naturales": 50.0, "punt_sociales_ciudadanas": 50.0, "punt_ingles": 50.0}
    return pd.DataFrame([row("ANTIOQUIA", 100, 55, 55), row("BOGOTÁ", 500, 60, 62),
                         row("TINY", 10, 90, 90), row("CHOCO", 40, 40, 42)])


def test_rank_departments():
    r = rank_departments(departments())
    assert r.n_departments == 3 and r.bogota_rank == 1
    assert r.table["department"].tolist() == ["BOGOTÁ", "ANTIOQUIA", "CHOCO"]
    assert r.table["rank"].tolist() == [1, 2, 3]
    assert r.table["math_reading"].iloc[0] == 122
    assert r.table["avg_5"].iloc[0] == pytest.approx((60 + 62 + 150) / 5)


def test_bogota_rank_none_when_absent():
    assert rank_departments(departments().iloc[[0, 3]]).bogota_rank is None


def bogota():
    def row(sede, est, m):
        return {"cole_cod_dane_sede": sede, "cole_cod_dane_establecimiento": est,
                **{s: m for s in SCORES}}
    return pd.DataFrame([row("111001000012.0", "x", 60.0), row("111001000012", "1", 40.0),
                         row("999", "211001000045", 50.0), row("888", "777", 70.0)])


def directory():
    return pd.DataFrame({"dane_sede": ["111001000012", ""], "dane_est": ["111001000012", "211001000045"],
                         "cod_localidad": ["01", "08"]})


def test_locality_results_sede_then_establishment():
    r = locality_results(bogota(), directory(), "http://dir")
    assert r.n_students == 4 and r.match_rate == 0.75 and r.directory_source == "http://dir"
    t = r.table
    usaquen = t[t["cod_localidad"] == "01"].iloc[0]
    assert usaquen["localidad"] == "Usaquén" and usaquen["n"] == 2 and usaquen["punt_ingles"] == 50.0
    assert t["avg_5"].tolist() == sorted(t["avg_5"], reverse=True)


class DirOk:
    def fetch(self):
        return directory(), "u"


class DirDown:
    def fetch(self):
        raise SourceUnavailableError("down")


def test_build_spatial_with_and_without_directory():
    assert build_spatial(departments(), bogota(), DirOk()).localities.match_rate == 0.75
    res = build_spatial(departments(), bogota(), DirDown())
    assert res.localities is None and res.departments.bogota_rank == 1

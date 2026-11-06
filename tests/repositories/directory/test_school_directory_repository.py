import pytest

from saber11.core.errors.pipeline_errors import SourceUnavailableError
from saber11.repositories.directory.school_directory_repository import SchoolDirectoryRepository
from tests.http.fake_http import FakeResponse, FakeSession

PACKAGE = {"result": {"resources": [
    {"format": "XLSX", "url": "http://x/dead.xlsx", "last_modified": "2030-01-01T00:00:00"},
    {"format": "GeoJSON", "url": "http://x/old.geojson", "last_modified": "2025-01-01T00:00:00"},
    {"format": "geojson", "url": "http://x/new.geojson", "last_modified": "2026-09-01T00:00:00"},
]}}
GEOJSON = {"features": [
    {"properties": {"DANE12_SED": "111001000012", "DANE12_EST": 111001000012.0, "COD_LOCA": "01"}},
    {"properties": {"DANE12_SED": None, "DANE12_EST": "211001000045", "COD_LOCA": "8"}},
]}


def test_picks_latest_geojson_and_normalizes():
    s = FakeSession([FakeResponse(PACKAGE), FakeResponse(GEOJSON)])
    df, url = SchoolDirectoryRepository(session=s).fetch()
    assert url == "http://x/new.geojson" and s.calls[1]["url"] == url
    assert list(df.columns) == ["dane_sede", "dane_est", "cod_localidad"]
    assert df["dane_est"].tolist() == ["111001000012", "211001000045"]
    assert df["cod_localidad"].tolist() == ["01", "08"]
    assert df["dane_sede"].iloc[1] == ""


def test_no_geojson_resource_raises():
    s = FakeSession([FakeResponse({"result": {"resources": [{"format": "XLSX", "url": "u"}]}})])
    with pytest.raises(SourceUnavailableError):
        SchoolDirectoryRepository(session=s).fetch()


def test_http_failure_raises():
    s = FakeSession([FakeResponse(status_code=404)])
    with pytest.raises(SourceUnavailableError):
        SchoolDirectoryRepository(session=s).fetch()


def test_fetch_reads_local_geojson_without_network(tmp_path):
    import json
    from saber11.repositories.directory.school_directory_repository import SchoolDirectoryRepository

    path = tmp_path / "colegios.geojson"
    feature = {"properties": {"DANE12_SED": "111001000132", "DANE12_EST": "111001000132", "COD_LOCA": "1"}}
    path.write_text(json.dumps({"features": [feature]}), encoding="utf-8")

    class NoNetwork:
        def get(self, *args, **kwargs):
            raise AssertionError("network must not be used")

    frame, source = SchoolDirectoryRepository(session=NoNetwork(), local_path=path).fetch()
    assert frame.to_dict("records") == [{"dane_sede": "111001000132", "dane_est": "111001000132", "cod_localidad": "01"}]
    assert source == str(path)

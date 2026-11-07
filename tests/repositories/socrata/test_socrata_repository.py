import pandas as pd
import pytest
import requests

from saber11.core.errors.pipeline_errors import SourceUnavailableError
from saber11.models.dataset.dataset_models import SCORES, STUDENT_COLUMNS
from saber11.repositories.socrata.socrata_repository import SocrataRepository
from tests.http.fake_http import FakeResponse, FakeSession


def row(i):
    return {c: str(i) for c in STUDENT_COLUMNS}


def repo(script, **kw):
    session = FakeSession(script)
    sleeps = []
    r = SocrataRepository(session=session, sleep=sleeps.append, page_size=2, **kw)
    return r, session, sleeps


def test_fetch_bogota_pages_until_empty_and_quotes_period():
    r, s, _ = repo([FakeResponse([row(1), row(2)]), FakeResponse([row(3)]), FakeResponse([])])
    df = r.fetch_bogota("20224")
    assert list(df.columns) == list(STUDENT_COLUMNS) and len(df) == 3
    first = s.calls[0]["params"]
    assert "periodo='20224'" in first["$where"] and "BOGOT" in first["$where"]
    assert [c["params"]["$offset"] for c in s.calls] == [0, 2, 4]
    assert first["$order"] == ":id" and first["$limit"] == 2


def test_missing_columns_are_filled_with_na():
    r, _, _ = repo([FakeResponse([{"periodo": "20224"}]), FakeResponse([])])
    df = r.fetch_bogota("20224")
    assert list(df.columns) == list(STUDENT_COLUMNS) and df["punt_ingles"].isna().all()


def test_app_token_header_sent():
    r, s, _ = repo([FakeResponse([])], app_token="tok")
    r.fetch_bogota("20224")
    assert s.calls[0]["headers"]["X-App-Token"] == "tok"


def test_retries_429_and_5xx_with_exponential_backoff():
    r, s, sleeps = repo([FakeResponse(status_code=429), FakeResponse(status_code=503),
                         requests.Timeout("t"), FakeResponse([])])
    assert r.fetch_bogota("20224").empty
    assert sleeps == [1, 2, 4] and len(s.calls) == 4


def test_gives_up_after_max_retries():
    r, _, sleeps = repo([FakeResponse(status_code=500)] * 3, max_retries=3)
    with pytest.raises(SourceUnavailableError):
        r.fetch_bogota("20224")
    assert len(sleeps) == 2


def test_client_error_is_not_retried():
    r, s, sleeps = repo([FakeResponse(status_code=400)])
    with pytest.raises(SourceUnavailableError):
        r.fetch_bogota("20224")
    assert sleeps == [] and len(s.calls) == 1


def test_fetch_department_means_numeric_and_renamed():
    payload = [{"cole_depto_ubicacion": "BOGOTÁ", "n": "70538",
                **{f"mean_{c}": "250.5" for c in SCORES}}]
    r, s, _ = repo([FakeResponse(payload)])
    df = r.fetch_department_means("20224")
    assert list(df.columns) == ["department", "n", *SCORES]
    assert df["n"].iloc[0] == 70538 and df["punt_ingles"].iloc[0] == 250.5
    p = s.calls[0]["params"]
    assert p["$group"] == "cole_depto_ubicacion" and p["$where"].startswith("periodo='20224'")
    assert "count(distinct estu_consecutivo)" in p["$select"]
    assert "'MAÑANA'" in p["$where"] and "NOCHE" not in p["$where"] and "punt_ingles IS NOT NULL" in p["$where"]
    assert isinstance(df, pd.DataFrame)


def test_fetch_bogota_selects_student_id():
    r, s, _ = repo([FakeResponse([])])
    r.fetch_bogota("20224")
    assert "estu_consecutivo" in s.calls[0]["params"]["$select"]


class NotJson(FakeResponse):
    def json(self):
        raise ValueError("Expecting value")


def test_non_json_body_is_retried_then_reported():
    r, s, sleeps = repo([NotJson(), FakeResponse([])])
    assert r.fetch_bogota("20224").empty and len(s.calls) == 2
    r, _, _ = repo([NotJson()] * 2, max_retries=2)
    with pytest.raises(SourceUnavailableError, match="not JSON"):
        r.fetch_bogota("20224")

from pathlib import Path

import pandas as pd
import pytest

from saber11.configs.pipeline.pipeline_config import PipelineConfig
from saber11.core.errors.pipeline_errors import DataValidationError
from saber11.models.dataset.dataset_models import SCORES, SHIFTS, STUDENT_COLUMNS
from saber11.services.ingestion.ingestion_service import (
    clean_students, department_means, draw_sample, ingest, is_bogota,
)


def students(n_per_shift=5, dept="BOGOTÁ", extra_shifts=("NOCHE",)):
    rows = []
    for shift in (*SHIFTS, *extra_shifts):
        for i in range(n_per_shift):
            rows.append({"periodo": "20224", "cole_depto_ubicacion": dept, "cole_jornada": shift,
                         "cole_cod_dane_sede": "1", "cole_cod_dane_establecimiento": "2",
                         "cole_naturaleza": "OFICIAL", **{s: str(40 + i) for s in SCORES}})
    return pd.DataFrame(rows)[list(STUDENT_COLUMNS)]


def test_clean_students_filters_shifts_scores_and_na():
    df = students()
    df.loc[0, "cole_jornada"] = " completa "
    df.loc[1, "punt_ingles"] = None
    df.loc[2, "punt_ingles"] = "abc"
    out = clean_students(df)
    assert set(out["cole_jornada"]) == set(SHIFTS)
    assert len(out) == 20 - 2 and out["punt_ingles"].dtype.kind == "f"
    assert list(out.columns) == list(STUDENT_COLUMNS)


def test_is_bogota_accent_insensitive():
    s = pd.Series(["BOGOTÁ", "BOGOTA D.C.", "Bogotá", "ANTIOQUIA", None])
    assert is_bogota(s).tolist() == [True, True, True, False, False]


def test_department_means():
    df = pd.concat([students(dept="A"), students(dept="B")])
    out = department_means(df)
    assert list(out.columns) == ["department", "n", *SCORES]
    assert out["n"].tolist() == [25, 25] and out["punt_ingles"].iloc[0] == 42.0


def test_draw_sample_reproducible_and_ordered():
    b = clean_students(students(10))
    a1, a2 = draw_sample(b, 4, 123), draw_sample(b, 4, 123)
    pd.testing.assert_frame_equal(a1, a2)
    assert a1["cole_jornada"].tolist() == [s for s in SHIFTS for _ in range(4)]
    assert a1.index.tolist() == list(range(16))


def test_draw_sample_too_small_raises():
    with pytest.raises(DataValidationError):
        draw_sample(clean_students(students(3)), 4, 1)


class FakeSocrata:
    def fetch_bogota(self, period):
        return students(6)

    def fetch_department_means(self, period):
        return pd.DataFrame({"department": ["BOGOTÁ"], "n": [24], **{s: [1.0] for s in SCORES}})


def test_ingest_api():
    cfg = PipelineConfig(sample_per_group=5)
    r = ingest(cfg, socrata=FakeSocrata())
    assert len(r.bogota) == 24 and len(r.sample) == 20
    assert r.departments["n"].iloc[0] == 24 and "20224" in r.source_detail


def test_ingest_dataicfes(tmp_path):
    df = pd.concat([students(6), students(6, dept="ANTIOQUIA")])
    class Repo:
        def __init__(self, path): self.path = path
        def read(self, period): return df
    cfg = PipelineConfig(source="dataicfes", dataicfes_path=tmp_path / "f.txt", sample_per_group=5)
    r = ingest(cfg, dataicfes_factory=Repo)
    assert len(r.bogota) == 24 and set(r.departments["department"]) == {"BOGOTÁ", "ANTIOQUIA"}
    assert "f.txt" in r.source_detail

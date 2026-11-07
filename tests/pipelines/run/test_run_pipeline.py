import json
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from saber11.configs.pipeline.pipeline_config import PipelineConfig
from saber11.models.dataset.dataset_models import (
    DANE_SCHOOL, DANE_SITE, DEPARTMENT, NATURE, SCORES, SHIFTS, SHIFT)
from saber11.models.dataset.ingestion_models import IngestionResult

for _mod in ("assumptions.assumptions_service", "descriptive.descriptive_service", "inference.manova_service",
             "inference.hotelling_service", "pca.pca_service", "spatial.spatial_service",
             "ingestion.ingestion_service"):
    pytest.importorskip(f"saber11.services.{_mod}")

from saber11.pipelines.run.run_pipeline import run  # noqa: E402

FIXTURE = Path(__file__).parents[2] / "fixtures" / "muestra_saber11_20224.csv"


class FakeDirectory:
    def fetch(self, *args, **kwargs):
        frame = pd.DataFrame({"dane_sede": ["111001000001"], "dane_est": ["111001000001"],
                              "cod_localidad": ["02"]})
        return frame, "https://example.org/dir.geojson"


def _fake_ingest(config):
    frame = pd.read_csv(FIXTURE)
    frame = frame[frame[SHIFT].isin(SHIFTS)].copy()
    frame[DANE_SITE] = "111001000001"
    frame[DANE_SCHOOL] = "111001000001"
    frame[NATURE] = "OFICIAL"
    rng = np.random.default_rng(0)
    depts = pd.DataFrame({"department": ["BOGOTÁ", "ANTIOQUIA", "VALLE"], "n": [len(frame), 900, 800],
                          **{s: rng.uniform(40, 60, 3) for s in SCORES}})
    sample = frame.groupby(SHIFT, group_keys=False).head(40)
    return IngestionResult(frame, sample, depts, "fixture 20224")


def test_run_writes_all_outputs(tmp_path):
    config = PipelineConfig(output_dir=tmp_path)
    art = run(config, ingest_fn=_fake_ingest, directory_repo=FakeDirectory(),
              now=lambda: datetime(2026, 11, 6, 10, 0, 0))
    assert art.pdf.read_bytes().startswith(b"%PDF")
    data = json.loads(art.results_json.read_text(encoding="utf-8"))
    assert data["metadata"]["generated_at"] == "2026-11-06T10:00:00"
    assert art.sample_csv.exists() and art.departments_csv.exists() and art.shift_summary_csv.exists()
    assert art.localities_csv is not None and art.localities_csv.exists()
    assert art.run_dir == tmp_path / "20224"


def test_run_leaves_no_partial_outputs_when_the_report_fails(tmp_path, monkeypatch):
    import saber11.pipelines.run.run_pipeline as pipeline

    def broken(results, path):
        raise RuntimeError("reportlab exploded")
    monkeypatch.setattr(pipeline, "render_pdf", broken)
    with pytest.raises(RuntimeError):
        run(PipelineConfig(output_dir=tmp_path), ingest_fn=_fake_ingest, directory_repo=FakeDirectory())
    finals = [p for p in (tmp_path / "20224").rglob("*") if p.is_file() and not p.name.endswith(".tmp")]
    assert finals == []


def test_results_json_includes_sensitivity(tmp_path):
    art = run(PipelineConfig(output_dir=tmp_path), ingest_fn=_fake_ingest, directory_repo=FakeDirectory())
    data = json.loads(art.results_json.read_text(encoding="utf-8"))
    assert data["sensitivity"]["official_only"]["manova"]["pillai"] > 0
    assert "mahalanobis_within" in data["assumptions"]
    assert not list((tmp_path / "20224").rglob("*.tmp"))

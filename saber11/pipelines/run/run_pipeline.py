"""Orchestrate ingestion, analysis, conclusions and output files."""

import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Callable

import pandas as pd

from saber11.configs.pipeline.pipeline_config import PipelineConfig
from saber11.models.dataset.dataset_models import SCORES, SHIFT
from saber11.models.dataset.ingestion_models import IngestionResult
from saber11.models.report.artifact_models import RunArtifacts
from saber11.models.report.report_models import PipelineResults, RunMetadata
from saber11.pipelines.run.results_serializer import to_jsonable
from saber11.renderers.report.pdf_renderer import render_pdf

log = logging.getLogger("saber11.pipeline")


def _default_ingest(config: PipelineConfig) -> IngestionResult:
    from saber11.services.ingestion.ingestion_service import ingest
    return ingest(config)


def _stage(name: str, fn: Callable, *args):
    """Run one stage and log a single JSON line with its duration."""
    start = time.perf_counter()
    result = fn(*args)
    print(json.dumps({"stage": name, "status": "ok", "seconds": round(time.perf_counter() - start, 3)}), flush=True)
    return result


def _analyze(config: PipelineConfig, ing: IngestionResult, directory_repo) -> dict:
    from saber11.services.assumptions.assumptions_service import check_assumptions
    from saber11.services.descriptive.descriptive_service import describe
    from saber11.services.inference.hotelling_service import pairwise_hotelling
    from saber11.services.inference.manova_service import run_manova
    from saber11.services.pca.pca_service import run_pca
    from saber11.services.spatial.spatial_service import build_spatial
    if directory_repo is None:
        from saber11.repositories.directory.school_directory_repository import SchoolDirectoryRepository
        directory_repo = SchoolDirectoryRepository(local_path=config.directory_path)
    a, s = config.alpha, ing.sample
    return {
        "descriptive": _stage("describe", describe, s, ing.bogota),
        "assumptions": _stage("assumptions", check_assumptions, s),
        "manova": _stage("manova", run_manova, s, a),
        "hotelling": _stage("hotelling", pairwise_hotelling, s, a),
        "pca": _stage("pca", run_pca, s),
        "spatial": _stage("spatial", build_spatial, ing.departments, ing.bogota, directory_repo,
                          config.sample_per_group, config.seed),
    }


def _shift_summary(bogota: pd.DataFrame) -> pd.DataFrame:
    grouped = bogota.groupby(SHIFT)
    out = grouped[list(SCORES)].mean()
    out.insert(0, "n", grouped.size())
    return out.reset_index()


def _write_data(config: PipelineConfig, ing: IngestionResult, results: PipelineResults) -> dict[str, Path | None]:
    data = config.run_dir / "data"
    data.mkdir(parents=True, exist_ok=True)
    p = config.period
    paths = {"sample_csv": data / f"muestra_saber11_{p}.csv",
             "shift_summary_csv": data / f"bogota_resumen_jornada_{p}.csv",
             "departments_csv": data / f"departamentos_saber11_{p}.csv", "localities_csv": None}
    ing.sample.to_csv(paths["sample_csv"], index=False)
    _shift_summary(ing.bogota).to_csv(paths["shift_summary_csv"], index=False)
    results.spatial.departments.table.to_csv(paths["departments_csv"], index=False)
    if results.spatial.localities is not None:
        paths["localities_csv"] = data / f"localidades_saber11_{p}.csv"
        results.spatial.localities.table.to_csv(paths["localities_csv"], index=False)
    return paths


def run(config: PipelineConfig, *, ingest_fn: Callable[[PipelineConfig], IngestionResult] = _default_ingest,
        directory_repo=None, now: Callable[[], datetime] = datetime.now) -> RunArtifacts:
    """Run the whole pipeline and write CSV, JSON and PDF outputs."""
    from saber11.services.conclusions.conclusions_service import draw_conclusions
    ing = _stage("ingest", ingest_fn, config)
    parts = _analyze(config, ing, directory_repo)
    conclusions = _stage("conclusions", draw_conclusions, parts["descriptive"], parts["assumptions"],
                         parts["manova"], parts["hotelling"], parts["pca"], parts["spatial"], config.alpha)
    meta = RunMetadata(config.period, config.source, ing.source_detail, len(ing.bogota),
                       config.sample_per_group, config.seed, config.alpha, now().isoformat(timespec="seconds"))
    results = PipelineResults(meta, conclusions=conclusions, **parts)
    config.run_dir.mkdir(parents=True, exist_ok=True)
    paths = _write_data(config, ing, results)
    json_path = config.run_dir / "results.json"
    json_path.write_text(json.dumps(to_jsonable(results), ensure_ascii=False, indent=2), encoding="utf-8")
    pdf = _stage("report", render_pdf, results, config.run_dir / f"informe_saber11_{config.period}.pdf")
    return RunArtifacts(config.run_dir, pdf, json_path, **paths)

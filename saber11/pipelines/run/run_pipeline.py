"""Orchestrate ingestion, analysis, conclusions and output files."""

import json
import logging
import os
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
TMP_SUFFIX = ".tmp"


def _default_ingest(config: PipelineConfig) -> IngestionResult:
    from saber11.services.ingestion.ingestion_service import ingest
    return ingest(config)


def _stage(name: str, fn: Callable, *args):
    """Run one stage and log a single JSON line with its duration."""
    start = time.perf_counter()
    result = fn(*args)
    log.info(json.dumps({"stage": name, "status": "ok", "seconds": round(time.perf_counter() - start, 3)}))
    return result


def _analyze(config: PipelineConfig, ing: IngestionResult, directory_repo) -> dict:
    from saber11.services.assumptions.assumptions_service import check_assumptions
    from saber11.services.descriptive.descriptive_service import describe
    from saber11.services.inference.hotelling_service import pairwise_hotelling
    from saber11.services.inference.manova_service import run_manova
    from saber11.services.pca.pca_service import run_pca
    from saber11.services.sensitivity.sensitivity_service import run_sensitivity
    from saber11.services.spatial.spatial_service import build_spatial
    if directory_repo is None:
        from saber11.repositories.directory.school_directory_repository import SchoolDirectoryRepository
        directory_repo = SchoolDirectoryRepository(local_path=config.directory_path)
    s, n, seed = ing.sample, config.sample_per_group, config.seed
    assumptions = _stage("assumptions", check_assumptions, s)
    return {
        "descriptive": _stage("describe", describe, s, ing.bogota),
        "assumptions": assumptions,
        "manova": _stage("manova", run_manova, s),
        "hotelling": _stage("hotelling", pairwise_hotelling, s),
        "pca": _stage("pca", run_pca, s),
        "spatial": _stage("spatial", build_spatial, ing.departments, ing.bogota, directory_repo, n, seed, config.alpha),
        "sensitivity": _stage("sensitivity", run_sensitivity, s, ing.bogota, assumptions, n, seed),
    }


def _shift_summary(bogota: pd.DataFrame) -> pd.DataFrame:
    grouped = bogota.groupby(SHIFT)
    out = grouped[list(SCORES)].mean()
    out.insert(0, "n", grouped.size())
    return out.reset_index()


def _tmp(path: Path) -> Path:
    return path.with_name(path.name + TMP_SUFFIX)


def _write_staged(config: PipelineConfig, ing: IngestionResult, results: PipelineResults) -> dict[str, Path | None]:
    """Write every output next to its final path with a .tmp suffix and return the final paths."""
    data, p = config.run_dir / "data", config.period
    data.mkdir(parents=True, exist_ok=True)
    loc = results.spatial.localities
    tables = {"sample_csv": (data / f"muestra_saber11_{p}.csv", ing.sample),
              "shift_summary_csv": (data / f"bogota_resumen_jornada_{p}.csv", _shift_summary(ing.bogota)),
              "departments_csv": (data / f"departamentos_saber11_{p}.csv", results.spatial.departments.table),
              "localities_csv": (data / f"localidades_saber11_{p}.csv", loc.table if loc else None)}
    paths: dict[str, Path | None] = {}
    for key, (path, frame) in tables.items():
        if frame is not None:
            frame.to_csv(_tmp(path), index=False)
        paths[key] = path if frame is not None else None
    paths["results_json"] = config.run_dir / "results.json"
    _tmp(paths["results_json"]).write_text(
        json.dumps(to_jsonable(results), ensure_ascii=False, indent=2), encoding="utf-8")
    return paths


def _publish(paths: list[Path]) -> None:
    """Move staged files into place only after every output was produced."""
    for path in paths:
        os.replace(_tmp(path), path)


def run(config: PipelineConfig, *, ingest_fn: Callable[[PipelineConfig], IngestionResult] = _default_ingest,
        directory_repo=None, now: Callable[[], datetime] = datetime.now) -> RunArtifacts:
    """Run the whole pipeline and write CSV, JSON and PDF outputs (all or nothing)."""
    from saber11.services.conclusions.conclusions_service import draw_conclusions
    ing = _stage("ingest", ingest_fn, config)
    parts = _analyze(config, ing, directory_repo)
    conclusions = _stage("conclusions", lambda: draw_conclusions(**parts, alpha=config.alpha, period=config.period))
    meta = RunMetadata(config.period, config.source, ing.source_detail, len(ing.bogota),
                       config.sample_per_group, config.seed, config.alpha, now().isoformat(timespec="seconds"))
    results = PipelineResults(meta, conclusions=conclusions, **parts)
    paths = _write_staged(config, ing, results)
    pdf = config.run_dir / f"informe_saber11_{config.period}.pdf"
    _stage("report", render_pdf, results, _tmp(pdf))
    _publish([pdf, *[path for path in paths.values() if path is not None]])
    return RunArtifacts(config.run_dir, pdf, **paths)

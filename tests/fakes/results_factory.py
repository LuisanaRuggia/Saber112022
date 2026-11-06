"""Build synthetic result dataclasses so report tests need no real services."""

import numpy as np
import pandas as pd

from saber11.models.analysis.analysis_models import (
    AnovaRow, AssumptionsResult, BoxMResult, DescriptiveResult, HotellingPair,
    MahalanobisResult, ManovaResult, MardiaResult, MultivariateTest, PcaResult,
)
from saber11.models.dataset.dataset_models import SCORES, SHIFTS
from saber11.models.report.report_models import PipelineResults, RunMetadata
from saber11.models.spatial.spatial_models import DepartmentRanking, LocalityResult, LocalityTestResult, LocalityTestRow, SpatialResult
from saber11.services.conclusions.conclusions_service import draw_conclusions


def _descriptive(shift_gap: float) -> DescriptiveResult:
    offsets = {"COMPLETA": shift_gap, "MAÑANA": 0.0, "TARDE": 0.0, "UNICA": 0.0}
    means = pd.DataFrame(
        {s: [50.0 + 2 * i + offsets[g] for g in SHIFTS] for i, s in enumerate(SCORES)}, index=list(SHIFTS))
    std = pd.DataFrame(10.0, index=list(SHIFTS), columns=list(SCORES))
    corr = pd.DataFrame(np.full((5, 5), 0.6) + 0.4 * np.eye(5), index=list(SCORES), columns=list(SCORES))
    return DescriptiveResult(
        n_by_group=dict.fromkeys(SHIFTS, 100), means=means, std=std,
        overall_mean=means.mean(), overall_std=std.mean(), covariance=corr * 100, correlation=corr,
        population_n_by_group={g: 1000 * (i + 1) for i, g in enumerate(SHIFTS)}, population_means=means)


def _manova(significant: bool) -> ManovaResult:
    p = 0.0001 if significant else 0.4
    names = ("Pillai's trace", "Wilks' lambda", "Hotelling-Lawley trace", "Roy's greatest root")
    tests = [MultivariateTest(n, 0.2, 5.0, 15.0, 1180.0, p) for n in names]
    anovas = [AnovaRow(s, 10.0, p, min(1.0, p * 5), 0.06) for s in SCORES]
    return ManovaResult(tests=tests, pillai=0.202, pillai_p=p, partial_eta_squared=0.067, anovas=anovas)


def _hotelling(significant: bool) -> list[HotellingPair]:
    pairs = []
    for i, a in enumerate(SHIFTS):
        for b in SHIFTS[i + 1:]:
            differs = significant and a == "COMPLETA"
            pb = 0.0001 if differs else 0.8
            diff = {s: (5.0 if differs else 0.2) for s in SCORES}
            pairs.append(HotellingPair(a, b, 30.0, 6.0, 5, 394, pb / 6, pb, diff))
    return pairs


def _pca(significant: bool) -> PcaResult:
    load = pd.DataFrame(
        {"PC1": [0.85, 0.9, 0.88, 0.89, 0.84], "PC2": [0.1, -0.2, 0.1, 0.0, 0.3]}, index=list(SCORES))
    means = {"COMPLETA": 1.0 if significant else 0.1, "MAÑANA": -0.2, "TARDE": -0.3, "UNICA": -0.1}
    return PcaResult([3.8, 0.5, 0.3, 0.2, 0.2], [0.765, 0.1, 0.06, 0.04, 0.035], load, means,
                     12.0, 0.00001 if significant else 0.5, 0.08)


def _spatial(with_localities: bool) -> SpatialResult:
    depts = pd.DataFrame({
        "department": ["BOGOTÁ", "SANTANDER", "CHOCÓ"], "n": [4000, 900, 300],
        **{s: [60.0, 58.0, 45.0] for s in SCORES}, "math_reading": [120.0, 116.0, 90.0],
        "avg_5": [60.0, 58.0, 45.0], "rank": [1, 2, 3]})
    loc = None
    if with_localities:
        table = pd.DataFrame({
            "cod_localidad": ["02", "08"], "localidad": ["Chapinero", "Kennedy"], "n": [500, 900],
            **{s: [65.0, 55.0] for s in SCORES}, "avg_5": [65.0, 55.0]})
        rows = [LocalityTestRow("avg_5", False, 3, 0.04, "Kruskal-Wallis", 85.2, 1e-9, 6e-9, 0.12, "ε²"),
                *[LocalityTestRow(s, True, 0, 0.3, "ANOVA", 4.1, 0.02, 0.12, 0.05, "η²") for s in SCORES]]
        tests = LocalityTestResult(rows, 100, 123, 200, 2, [])
        loc = LocalityResult(table, 0.93, 4000, "https://example.org/dir.geojson", tests)
    return SpatialResult(DepartmentRanking(depts, 1, 3), loc)


def build_results(significant: bool = True, with_localities: bool = True) -> PipelineResults:
    """Return a full synthetic PipelineResults."""
    desc = _descriptive(8.0 if significant else 0.1)
    assumptions = AssumptionsResult(
        MahalanobisResult(14.4, 0.975, 15, 3.75, [1, 2]),
        MardiaResult(1.2, 80.0, 0.001, 36.0, 3.0, 0.002, {g: (0.2, 0.3) for g in SHIFTS}),
        BoxMResult(50.0, 45.0, 30, 0.238))
    manova, hot, pca, spatial = _manova(significant), _hotelling(significant), _pca(significant), _spatial(with_localities)
    conclusions = draw_conclusions(desc, assumptions, manova, hot, pca, spatial, 0.05)
    meta = RunMetadata("20224", "api", "datos.gov.co", 10000, 100, 123, 0.05, "2026-11-06T10:00:00")
    return PipelineResults(meta, desc, assumptions, manova, hot, pca, spatial, conclusions)

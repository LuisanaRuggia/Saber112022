"""Descriptive statistics of the sample and the population by shift."""

import pandas as pd

from saber11.core.errors.pipeline_errors import DataValidationError
from saber11.models.analysis.analysis_models import DescriptiveResult
from saber11.models.dataset.dataset_models import SCORES, SHIFT, SHIFTS


def _present_shifts(frame: pd.DataFrame) -> list[str]:
    """Return the shifts present in the frame, in canonical order."""
    missing = [column for column in (SHIFT, *SCORES) if column not in frame.columns]
    if missing:
        raise DataValidationError(f"Missing columns: {missing}")
    present = set(frame[SHIFT])
    return [shift for shift in SHIFTS if shift in present]


def _grouped(frame: pd.DataFrame, statistic: str) -> pd.DataFrame:
    """Aggregate scores per shift with the canonical row order."""
    shifts = _present_shifts(frame)
    subset = frame[frame[SHIFT].isin(shifts)]
    table = subset.groupby(SHIFT)[list(SCORES)].agg(statistic)
    return table.reindex(shifts).astype(float)


def _counts(frame: pd.DataFrame) -> dict[str, int]:
    """Count rows per present shift."""
    counts = frame[SHIFT].value_counts()
    return {shift: int(counts[shift]) for shift in _present_shifts(frame)}


def describe(sample: pd.DataFrame, population: pd.DataFrame) -> DescriptiveResult:
    """Summarize the sample by shift and the population means by shift."""
    if sample.empty:
        raise DataValidationError("Sample is empty")
    scores = sample[sample[SHIFT].isin(SHIFTS)][list(SCORES)].astype(float)
    return DescriptiveResult(
        n_by_group=_counts(sample),
        means=_grouped(sample, "mean"),
        std=_grouped(sample, "std"),
        overall_mean=scores.mean(),
        overall_std=scores.std(ddof=1),
        covariance=scores.cov(ddof=1),
        correlation=scores.corr(),
        population_n_by_group=_counts(population),
        population_means=_grouped(population, "mean"),
    )

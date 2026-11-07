"""Split a sample into per-shift score matrices, validated for multivariate tests."""

import numpy as np
import pandas as pd

from saber11.core.errors.pipeline_errors import DataValidationError
from saber11.models.dataset.dataset_models import SCORES, SHIFT, SHIFTS


def split_by_shift(sample: pd.DataFrame, purpose: str) -> dict[str, np.ndarray]:
    """Return {shift: scores} in canonical order; need two shifts with more rows than scores."""
    groups = {
        shift: sample.loc[sample[SHIFT] == shift, list(SCORES)].to_numpy(float)
        for shift in SHIFTS
        if (sample[SHIFT] == shift).any()
    }
    if len(groups) < 2:
        raise DataValidationError(f"{purpose} needs at least two shifts")
    for shift, values in groups.items():
        if len(values) <= len(SCORES):
            raise DataValidationError(f"Shift {shift} has {len(values)} rows; need more than {len(SCORES)}")
    return groups


def within_residuals(sample: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return residuals from each shift mean, their row positions and the pooled within-shift covariance."""
    mask = sample[SHIFT].isin(SHIFTS).to_numpy()
    frame = sample.loc[mask, [SHIFT, *SCORES]]
    values = frame[list(SCORES)].to_numpy(float)
    residuals = values - frame.groupby(SHIFT)[list(SCORES)].transform("mean").to_numpy(float)
    n_groups = frame[SHIFT].nunique()
    pooled = residuals.T @ residuals / (len(residuals) - n_groups)
    return residuals, np.flatnonzero(mask), pooled

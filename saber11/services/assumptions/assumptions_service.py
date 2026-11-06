"""Assumption checks for MANOVA: outliers, multivariate normality and covariance homogeneity."""

import numpy as np
import pandas as pd
from scipy import stats

from saber11.core.errors.pipeline_errors import DataValidationError
from saber11.models.analysis.analysis_models import (
    AssumptionsResult,
    BoxMResult,
    MahalanobisResult,
    MardiaResult,
)
from saber11.models.dataset.dataset_models import SCORES, SHIFT, SHIFTS


def _groups(sample: pd.DataFrame) -> dict[str, np.ndarray]:
    """Split the scores by shift, requiring more rows than variables per group."""
    groups = {
        shift: sample.loc[sample[SHIFT] == shift, list(SCORES)].to_numpy(float)
        for shift in SHIFTS
        if (sample[SHIFT] == shift).any()
    }
    for shift, values in groups.items():
        if len(values) <= len(SCORES):
            raise DataValidationError(f"Shift {shift} has {len(values)} rows; need more than {len(SCORES)}")
    if not groups:
        raise DataValidationError("No compared shifts present in sample")
    return groups


def _squared_distances(values: np.ndarray, covariance: np.ndarray) -> np.ndarray:
    """Return squared Mahalanobis distances of each row to the column means."""
    centered = values - values.mean(axis=0)
    return np.einsum("ij,jk,ik->i", centered, np.linalg.inv(covariance), centered)


def mahalanobis(values: np.ndarray, quantile: float, positions: np.ndarray) -> MahalanobisResult:
    """Flag rows whose squared distance exceeds the chi-square quantile."""
    distances = _squared_distances(values, np.cov(values, rowvar=False, ddof=1))
    threshold = float(stats.chi2.ppf(quantile, values.shape[1]))
    outliers = np.flatnonzero(distances > threshold)
    return MahalanobisResult(
        threshold=threshold,
        quantile=quantile,
        n_outliers=len(outliers),
        pct_outliers=100.0 * len(outliers) / len(values),
        outlier_index=[int(positions[index]) for index in outliers],
    )


def _mardia_stats(values: np.ndarray) -> tuple[float, float, float, float, float, float]:
    """Compute Mardia's b1p, b2p and their statistics and p-values."""
    n, p = values.shape
    centered = values - values.mean(axis=0)
    # Mardia's coefficients are defined with the biased (divide-by-n) covariance.
    gram = centered @ np.linalg.inv(np.cov(values, rowvar=False, ddof=0)) @ centered.T
    b1p = float((gram**3).sum() / n**2)
    b2p = float((np.diag(gram) ** 2).sum() / n)
    skew_stat = n * b1p / 6
    skew_p = float(stats.chi2.sf(skew_stat, p * (p + 1) * (p + 2) / 6))
    kurt_stat = (b2p - p * (p + 2)) / np.sqrt(8 * p * (p + 2) / n)
    kurt_p = float(2 * stats.norm.sf(abs(kurt_stat)))
    return b1p, skew_stat, skew_p, b2p, float(kurt_stat), kurt_p


def mardia(values: np.ndarray, groups: dict[str, np.ndarray]) -> MardiaResult:
    """Run Mardia's tests on the whole sample and on each group."""
    b1p, skew_stat, skew_p, b2p, kurt_stat, kurt_p = _mardia_stats(values)
    by_group = {}
    for shift, group in groups.items():
        group_stats = _mardia_stats(group)
        by_group[shift] = (group_stats[2], group_stats[5])
    return MardiaResult(b1p, skew_stat, skew_p, b2p, kurt_stat, kurt_p, by_group)


def box_m(groups: dict[str, np.ndarray]) -> BoxMResult:
    """Run Box's M test with the chi-square approximation."""
    sizes = np.array([len(group) for group in groups.values()])
    covariances = [np.cov(group, rowvar=False, ddof=1) for group in groups.values()]
    k, p, total = len(sizes), covariances[0].shape[0], sizes.sum()
    pooled = sum((n - 1) * cov for n, cov in zip(sizes, covariances)) / (total - k)
    log_dets = [np.linalg.slogdet(cov)[1] for cov in covariances]
    m = (total - k) * np.linalg.slogdet(pooled)[1] - sum((n - 1) * d for n, d in zip(sizes, log_dets))
    correction = (np.sum(1 / (sizes - 1)) - 1 / (total - k)) * (2 * p**2 + 3 * p - 1) / (6 * (p + 1) * (k - 1))
    chi2 = m * (1 - correction)
    df = int(p * (p + 1) * (k - 1) / 2)
    return BoxMResult(m=float(m), chi2=float(chi2), df=df, p_value=float(stats.chi2.sf(chi2, df)))


def check_assumptions(sample: pd.DataFrame, quantile: float = 0.975) -> AssumptionsResult:
    """Run Mahalanobis outlier detection, Mardia's tests and Box's M."""
    groups = _groups(sample)
    if len(groups) < 2:
        raise DataValidationError("Box's M needs at least two shifts")
    values = np.vstack(list(groups.values()))
    # Outlier indices must be positions in the caller's frame, including excluded rows.
    mask = sample[SHIFT].isin(list(groups)).to_numpy()
    in_scope = sample.loc[mask, list(SCORES)].to_numpy(float)
    return AssumptionsResult(
        mahalanobis=mahalanobis(in_scope, quantile, np.flatnonzero(mask)),
        mardia=mardia(values, groups),
        box_m=box_m(groups),
    )

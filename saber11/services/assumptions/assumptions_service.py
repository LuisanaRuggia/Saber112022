"""Assumption checks for MANOVA: outliers, multivariate normality and covariance homogeneity."""

import numpy as np
import pandas as pd
from scipy import stats

from saber11.models.analysis.analysis_models import (
    AssumptionsResult,
    BoxMResult,
    MahalanobisResult,
    MardiaResult,
)
from saber11.models.dataset.dataset_models import SCORES
from saber11.services.groups.shift_groups import split_by_shift, within_residuals


def _squared_distances(values: np.ndarray, covariance: np.ndarray) -> np.ndarray:
    """Return squared Mahalanobis distances of each row to the column means."""
    centered = values - values.mean(axis=0)
    return np.einsum("ij,jk,ik->i", centered, np.linalg.inv(covariance), centered)


def mahalanobis(values: np.ndarray, quantile: float, positions: np.ndarray,
                covariance: np.ndarray | None = None) -> MahalanobisResult:
    """Flag rows whose squared distance exceeds the chi-square quantile.

    Without `covariance` the total sample covariance is used, as in the course guide.
    """
    if covariance is None:
        covariance = np.cov(values, rowvar=False, ddof=1)
    distances = _squared_distances(values, covariance)
    threshold = float(stats.chi2.ppf(quantile, values.shape[1]))
    outliers = np.flatnonzero(distances > threshold)
    return MahalanobisResult(
        threshold=threshold,
        quantile=quantile,
        n_outliers=len(outliers),
        pct_outliers=100.0 * len(outliers) / len(values),
        outlier_index=[int(positions[index]) for index in outliers],
        squared_distances=[float(d) for d in distances],
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
    """Run Mardia's tests on `values` and on each group (pass {} to skip the groups)."""
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
    """Run Mahalanobis, Mardia and Box's M, both as in the guide and on within-shift residuals."""
    groups = split_by_shift(sample, "Box's M")
    values = np.vstack(list(groups.values()))
    # Outlier indices must be positions in the caller's frame, including excluded rows.
    residuals, positions, pooled = within_residuals(sample)
    in_scope = sample.iloc[positions][list(SCORES)].to_numpy(float)
    return AssumptionsResult(
        mahalanobis=mahalanobis(in_scope, quantile, positions),
        mardia=mardia(values, groups),
        box_m=box_m(groups),
        mahalanobis_within=mahalanobis(residuals, quantile, positions, pooled),
        mardia_within=mardia(residuals, {}),
    )

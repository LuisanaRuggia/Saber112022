"""Principal component analysis on the correlation matrix and ANOVA of PC1 by shift."""

import numpy as np
import pandas as pd
from scipy import stats

from saber11.core.errors.pipeline_errors import DataValidationError
from saber11.models.analysis.analysis_models import PcaResult
from saber11.models.dataset.dataset_models import SCORES, SHIFT, SHIFTS


def _standardized(frame: pd.DataFrame) -> np.ndarray:
    """Standardize the scores with the sample standard deviation."""
    values = frame[list(SCORES)].to_numpy(float)
    std = values.std(axis=0, ddof=1)
    if len(values) < 2 or (std == 0).any():
        raise DataValidationError("PCA needs at least two rows and non-constant scores")
    return (values - values.mean(axis=0)) / std


def _eigen(standardized: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Eigen-decompose the correlation matrix, sorted descending, PC1 oriented positive."""
    eigenvalues, eigenvectors = np.linalg.eigh(np.corrcoef(standardized, rowvar=False))
    order = np.argsort(eigenvalues)[::-1]
    eigenvalues, eigenvectors = eigenvalues[order], eigenvectors[:, order]
    # Eigenvector signs are arbitrary; fix PC1 so it reads as "overall performance".
    if eigenvectors[:, 0].sum() < 0:
        eigenvectors[:, 0] *= -1
    return eigenvalues, eigenvectors


def _pc1_anova(pc1: np.ndarray, labels: np.ndarray, shifts: list[str]) -> tuple[float, float, float]:
    """Run a one-way ANOVA of PC1 scores by shift and return F, p and eta squared."""
    groups = [pc1[labels == shift] for shift in shifts]
    if len(groups) < 2:
        return float("nan"), float("nan"), float("nan")
    f_value, p_value = stats.f_oneway(*groups)
    ss_between = sum(len(group) * (group.mean() - pc1.mean()) ** 2 for group in groups)
    return float(f_value), float(p_value), float(ss_between / ((pc1 - pc1.mean()) ** 2).sum())


def run_pca(sample: pd.DataFrame) -> PcaResult:
    """Extract principal components of the scores and compare PC1 across shifts."""
    frame = sample[sample[SHIFT].isin(SHIFTS)]
    standardized = _standardized(frame)
    eigenvalues, eigenvectors = _eigen(standardized)
    columns = [f"PC{index + 1}" for index in range(len(SCORES))]
    loadings = pd.DataFrame(eigenvectors * np.sqrt(eigenvalues), index=list(SCORES), columns=columns)
    pc1 = standardized @ eigenvectors[:, 0]
    labels = frame[SHIFT].to_numpy()
    shifts = [shift for shift in SHIFTS if (labels == shift).any()]
    f_value, p_value, eta_squared = _pc1_anova(pc1, labels, shifts)
    return PcaResult(
        eigenvalues=[float(value) for value in eigenvalues],
        explained_ratio=[float(value / eigenvalues.sum()) for value in eigenvalues],
        loadings=loadings,
        cp1_means={shift: float(pc1[labels == shift].mean()) for shift in shifts},
        cp1_f=f_value,
        cp1_p=p_value,
        cp1_eta_squared=eta_squared,
    )

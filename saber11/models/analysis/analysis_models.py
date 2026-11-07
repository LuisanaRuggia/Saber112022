"""Result contracts produced by the analysis services and consumed by the report."""

from dataclasses import dataclass, field

import pandas as pd


@dataclass(frozen=True)
class DescriptiveResult:
    """Sample and population descriptive statistics."""

    n_by_group: dict[str, int]
    means: pd.DataFrame            # rows: shifts, cols: scores
    std: pd.DataFrame              # rows: shifts, cols: scores
    overall_mean: pd.Series        # index: scores
    overall_std: pd.Series
    covariance: pd.DataFrame       # total sample covariance, ignoring shifts (scores x scores)
    correlation: pd.DataFrame
    population_n_by_group: dict[str, int]
    population_means: pd.DataFrame  # full Bogotá population, rows: shifts


@dataclass(frozen=True)
class MahalanobisResult:
    """Multivariate outliers by squared Mahalanobis distance."""

    threshold: float
    quantile: float
    n_outliers: int
    pct_outliers: float  # percentage on a 0-100 scale
    outlier_index: list[int] = field(default_factory=list)


@dataclass(frozen=True)
class MardiaResult:
    """Mardia's multivariate skewness and kurtosis tests."""

    skewness: float
    skewness_stat: float
    skewness_p: float
    kurtosis: float
    kurtosis_stat: float
    kurtosis_p: float
    by_group: dict[str, tuple[float, float]]  # shift -> (skew p, kurt p)


@dataclass(frozen=True)
class BoxMResult:
    """Box's M test for equality of covariance matrices."""

    m: float
    chi2: float
    df: int
    p_value: float


@dataclass(frozen=True)
class AssumptionsResult:
    """All assumption checks.

    `mahalanobis` and `mardia` follow the course guide (total covariance, so shift mean
    differences inflate them); the `_within` variants use residuals from each shift mean
    and the pooled within-shift covariance, which is what MANOVA actually assumes.
    """

    mahalanobis: MahalanobisResult
    mardia: MardiaResult
    box_m: BoxMResult
    mahalanobis_within: MahalanobisResult
    mardia_within: MardiaResult


@dataclass(frozen=True)
class MultivariateTest:
    """One MANOVA statistic row."""

    name: str
    value: float
    f_value: float
    df_num: float
    df_den: float
    p_value: float


@dataclass(frozen=True)
class AnovaRow:
    """Follow-up univariate ANOVA for one score."""

    score: str
    f_value: float
    p_value: float
    p_bonferroni: float
    eta_squared: float


@dataclass(frozen=True)
class ManovaResult:
    """MANOVA statistics plus follow-up ANOVAs."""

    tests: list[MultivariateTest]
    pillai: float
    pillai_p: float
    partial_eta_squared: float
    anovas: list[AnovaRow]


@dataclass(frozen=True)
class HotellingPair:
    """Two-sample Hotelling T² for one pair of shifts."""

    group_a: str
    group_b: str
    t2: float
    f_value: float
    df1: int
    df2: int
    p_value: float
    p_bonferroni: float
    mean_difference: dict[str, float]  # score -> mean(a) - mean(b)


@dataclass(frozen=True)
class PcaResult:
    """PCA on the correlation matrix and ANOVA on the first component."""

    eigenvalues: list[float]
    explained_ratio: list[float]
    loadings: pd.DataFrame          # rows: scores, cols: PC1..PCp (eigvec * sqrt(eigval))
    cp1_means: dict[str, float]     # shift -> mean PC1 score
    cp1_f: float
    cp1_p: float
    cp1_eta_squared: float

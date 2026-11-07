"""Result contracts of the sensitivity analyses that probe the main MANOVA."""

from dataclasses import dataclass

import pandas as pd

from saber11.models.analysis.analysis_models import HotellingPair, ManovaResult


@dataclass(frozen=True)
class OutlierSensitivity:
    """MANOVA repeated without the within-shift Mahalanobis outliers."""

    n_removed: int
    manova: ManovaResult


@dataclass(frozen=True)
class NatureSensitivity:
    """School nature (public or private) by shift, and the analysis restricted to public schools."""

    profile: pd.DataFrame        # rows: shifts; cols: n, n_official, n_private, share_private
    means: pd.DataFrame          # rows: (nature, shift); cols: n, <scores>
    official_shifts: list[str]   # shifts with enough public-school students to sample
    n_sample: int
    manova: ManovaResult | None  # None when fewer than two shifts qualify
    hotelling: list[HotellingPair]


@dataclass(frozen=True)
class SensitivityResult:
    """Every robustness check of the main result."""

    without_outliers: OutlierSensitivity
    official_only: NatureSensitivity

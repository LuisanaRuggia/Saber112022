"""Pairwise two-sample Hotelling T² tests between shifts with Bonferroni correction."""

from itertools import combinations

import numpy as np
import pandas as pd
from scipy import stats

from saber11.models.analysis.analysis_models import HotellingPair
from saber11.models.dataset.dataset_models import SCORES
from saber11.services.groups.shift_groups import split_by_shift


def _t2(first: np.ndarray, second: np.ndarray) -> tuple[float, np.ndarray]:
    """Return T² with pooled covariance and the mean difference vector."""
    n1, n2 = len(first), len(second)
    pooled = ((n1 - 1) * np.cov(first, rowvar=False) + (n2 - 1) * np.cov(second, rowvar=False)) / (n1 + n2 - 2)
    difference = first.mean(axis=0) - second.mean(axis=0)
    t2 = (n1 * n2 / (n1 + n2)) * difference @ np.linalg.solve(pooled, difference)
    return float(t2), difference


def _pair(name_a: str, first: np.ndarray, name_b: str, second: np.ndarray, n_pairs: int) -> HotellingPair:
    """Build one pair result with the F transformation and Bonferroni p."""
    p, n1, n2 = first.shape[1], len(first), len(second)
    t2, difference = _t2(first, second)
    df2 = n1 + n2 - p - 1
    f_value = df2 / (p * (n1 + n2 - 2)) * t2
    p_value = float(stats.f.sf(f_value, p, df2))
    return HotellingPair(
        group_a=name_a,
        group_b=name_b,
        t2=t2,
        f_value=float(f_value),
        df1=p,
        df2=df2,
        p_value=p_value,
        p_bonferroni=min(1.0, p_value * n_pairs),
        mean_difference={score: float(value) for score, value in zip(SCORES, difference)},
    )


def pairwise_hotelling(sample: pd.DataFrame) -> list[HotellingPair]:
    """Compare every pair of shifts with Bonferroni over the number of pairs."""
    groups = split_by_shift(sample, "Hotelling T²")
    pairs = list(combinations(groups, 2))
    return [_pair(a, groups[a], b, groups[b], len(pairs)) for a, b in pairs]

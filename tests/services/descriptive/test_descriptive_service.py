"""Tests for the descriptive statistics service."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from saber11.models.dataset.dataset_models import SCORES, SHIFT, SHIFTS
from saber11.services.descriptive.descriptive_service import describe

FIXTURE = Path(__file__).parents[2] / "fixtures" / "muestra_saber11_20224.csv"


@pytest.fixture(scope="module")
def sample() -> pd.DataFrame:
    """Load the 2022 sample restricted to the compared shifts."""
    data = pd.read_csv(FIXTURE)
    return data[data[SHIFT].isin(SHIFTS)].reset_index(drop=True)


def test_group_sizes_and_order(sample):
    result = describe(sample, sample)
    assert result.n_by_group == {shift: 100 for shift in SHIFTS}
    assert list(result.means.index) == list(SHIFTS)
    assert list(result.means.columns) == list(SCORES)


def test_matches_pandas(sample):
    result = describe(sample, sample)
    expected = sample[list(SCORES)].cov()
    np.testing.assert_allclose(result.covariance.to_numpy(), expected.to_numpy())
    np.testing.assert_allclose(result.overall_std, sample[list(SCORES)].std())
    assert result.correlation.loc["punt_ingles", "punt_ingles"] == pytest.approx(1.0)


def test_largest_gap_is_english(sample):
    means = describe(sample, sample).means
    assert means.loc["COMPLETA", "punt_ingles"] == pytest.approx(66.0, abs=0.05)
    assert means.loc["TARDE", "punt_ingles"] == pytest.approx(52.2, abs=0.05)
    gaps = means.max() - means.min()
    assert gaps.idxmax() == "punt_ingles"


def test_population_summary_uses_population(sample):
    population = pd.concat([sample, sample[sample[SHIFT] == "TARDE"]])
    result = describe(sample, population)
    assert result.population_n_by_group["TARDE"] == 200
    assert list(result.population_means.index) == list(SHIFTS)


def test_only_present_shifts_kept(sample):
    subset = sample[sample[SHIFT].isin(["UNICA", "MAÑANA"])]
    result = describe(subset, subset)
    assert list(result.means.index) == ["MAÑANA", "UNICA"]

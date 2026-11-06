"""Tests for the assumption checks (Mahalanobis, Mardia, Box's M)."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from saber11.core.errors.pipeline_errors import DataValidationError
from saber11.models.dataset.dataset_models import SCORES, SHIFT, SHIFTS
from saber11.services.assumptions.assumptions_service import check_assumptions

FIXTURE = Path(__file__).parents[2] / "fixtures" / "muestra_saber11_20224.csv"


@pytest.fixture(scope="module")
def sample() -> pd.DataFrame:
    """Load the 2022 sample restricted to the compared shifts."""
    data = pd.read_csv(FIXTURE)
    return data[data[SHIFT].isin(SHIFTS)].reset_index(drop=True)


@pytest.fixture(scope="module")
def result(sample):
    """Run the checks once on the fixture."""
    return check_assumptions(sample)


def synthetic(seed: int, groups=SHIFTS, n: int = 60) -> pd.DataFrame:
    """Build normal groups drawn from one shared distribution."""
    rng = np.random.default_rng(seed)
    values = rng.normal(50, 10, size=(n * len(groups), len(SCORES)))
    frame = pd.DataFrame(values, columns=list(SCORES))
    frame[SHIFT] = np.repeat(groups, n)
    return frame


def test_mahalanobis_outliers(result):
    maha = result.mahalanobis
    assert maha.n_outliers == 15
    assert maha.pct_outliers == pytest.approx(3.75)
    assert len(maha.outlier_index) == 15
    assert maha.quantile == 0.975


def test_mardia_rejects_normality(result):
    mardia = result.mardia
    assert min(mardia.skewness_p, mardia.kurtosis_p) < 0.001
    assert list(mardia.by_group) == list(SHIFTS)


def test_box_m_not_rejected(result):
    box = result.box_m
    assert box.p_value == pytest.approx(0.238, abs=0.0005)
    assert box.df == 45


def test_identical_groups_box_m_zero():
    block = synthetic(1, groups=("COMPLETA",))
    frame = pd.concat([block.assign(**{SHIFT: shift}) for shift in SHIFTS])
    box = check_assumptions(frame).box_m
    assert box.m == pytest.approx(0.0, abs=1e-8)
    assert box.p_value == pytest.approx(1.0)


def test_mardia_accepts_normal_data():
    mardia = check_assumptions(synthetic(2, n=150)).mardia
    assert mardia.skewness_p > 0.01 and mardia.kurtosis_p > 0.01


def test_group_too_small_raises():
    frame = synthetic(3)
    frame = pd.concat([frame[frame[SHIFT] != "TARDE"], frame[frame[SHIFT] == "TARDE"].head(4)])
    with pytest.raises(DataValidationError):
        check_assumptions(frame)

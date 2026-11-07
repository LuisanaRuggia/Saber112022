"""Tests for the MANOVA service."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from saber11.core.errors.pipeline_errors import DataValidationError
from saber11.models.dataset.dataset_models import SCORES, SHIFT, SHIFTS
from saber11.services.inference.manova_service import run_manova

FIXTURE = Path(__file__).parents[2] / "fixtures" / "muestra_saber11_20224.csv"


@pytest.fixture(scope="module")
def sample() -> pd.DataFrame:
    """Load the 2022 sample restricted to the compared shifts."""
    data = pd.read_csv(FIXTURE)
    return data[data[SHIFT].isin(SHIFTS)].reset_index(drop=True)


@pytest.fixture(scope="module")
def result(sample):
    """Run MANOVA once on the fixture."""
    return run_manova(sample)


def test_pillai_matches_published(result):
    assert result.pillai == pytest.approx(0.202, abs=0.0005)
    assert result.pillai_p < 0.001
    assert result.partial_eta_squared == pytest.approx(0.067, abs=0.0005)


def test_four_statistics_reported(result):
    names = [test.name for test in result.tests]
    assert names == ["Pillai's trace", "Wilks' lambda", "Hotelling-Lawley trace", "Roy's greatest root"]
    assert all(test.df_num > 0 and test.df_den > 0 for test in result.tests)


def test_identical_groups_not_significant():
    rng = np.random.default_rng(7)
    frame = pd.DataFrame(rng.normal(50, 10, size=(240, 5)), columns=list(SCORES))
    frame[SHIFT] = np.repeat(SHIFTS, 60)
    assert run_manova(frame).pillai_p > 0.05


def test_single_group_raises(sample):
    with pytest.raises(DataValidationError):
        run_manova(sample[sample[SHIFT] == "TARDE"])

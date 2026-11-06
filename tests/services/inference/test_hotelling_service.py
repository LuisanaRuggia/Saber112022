"""Tests for pairwise Hotelling T²."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from saber11.core.errors.pipeline_errors import DataValidationError
from saber11.models.dataset.dataset_models import SCORES, SHIFT, SHIFTS
from saber11.services.inference.hotelling_service import pairwise_hotelling

FIXTURE = Path(__file__).parents[2] / "fixtures" / "muestra_saber11_20224.csv"


@pytest.fixture(scope="module")
def pairs() -> dict:
    """Run all pairs on the 2022 sample keyed by (a, b)."""
    data = pd.read_csv(FIXTURE)
    sample = data[data[SHIFT].isin(SHIFTS)].reset_index(drop=True)
    return {(pair.group_a, pair.group_b): pair for pair in pairwise_hotelling(sample)}


def test_six_pairs_in_shift_order(pairs):
    assert list(pairs) == [
        ("COMPLETA", "MAÑANA"), ("COMPLETA", "TARDE"), ("COMPLETA", "UNICA"),
        ("MAÑANA", "TARDE"), ("MAÑANA", "UNICA"), ("TARDE", "UNICA"),
    ]


def test_completa_differs_from_others(pairs):
    for other in ("MAÑANA", "TARDE", "UNICA"):
        assert pairs[("COMPLETA", other)].p_bonferroni < 0.001


def test_other_shifts_do_not_differ(pairs):
    for key in (("MAÑANA", "TARDE"), ("MAÑANA", "UNICA"), ("TARDE", "UNICA")):
        assert pairs[key].p_bonferroni >= 0.99


def test_pair_fields(pairs):
    pair = pairs[("COMPLETA", "TARDE")]
    assert (pair.df1, pair.df2) == (5, 194)
    assert pair.mean_difference["punt_ingles"] == pytest.approx(13.8, abs=0.1)
    assert pair.f_value == pytest.approx(pair.t2 * 194 / (5 * 198))


def test_identical_groups_large_p():
    rng = np.random.default_rng(11)
    block = rng.normal(50, 10, size=(50, 5))
    frame = pd.DataFrame(np.vstack([block, block]), columns=list(SCORES))
    frame[SHIFT] = np.repeat(["MAÑANA", "TARDE"], 50)
    (pair,) = pairwise_hotelling(frame)
    assert pair.t2 == pytest.approx(0.0, abs=1e-9)
    assert pair.p_value == pytest.approx(1.0)


def test_too_small_group_raises():
    rng = np.random.default_rng(12)
    frame = pd.DataFrame(rng.normal(50, 10, size=(23, 5)), columns=list(SCORES))
    frame[SHIFT] = ["MAÑANA"] * 20 + ["TARDE"] * 3
    with pytest.raises(DataValidationError):
        pairwise_hotelling(frame)

import numpy as np
import pandas as pd
import pytest

from saber11.core.errors.pipeline_errors import DataValidationError
from saber11.models.dataset.dataset_models import SCORES, SHIFT
from saber11.services.groups.shift_groups import split_by_shift, within_residuals


def _frame(shifts, n=10, seed=0):
    rng = np.random.default_rng(seed)
    frame = pd.DataFrame(rng.normal(50, 10, size=(n * len(shifts), len(SCORES))), columns=list(SCORES))
    frame[SHIFT] = np.repeat(shifts, n)
    return frame


def test_split_keeps_canonical_order_and_skips_absent_shifts():
    groups = split_by_shift(_frame(["UNICA", "COMPLETA"]), "test")
    assert list(groups) == ["COMPLETA", "UNICA"] and groups["UNICA"].shape == (10, 5)


@pytest.mark.parametrize("shifts,n", [(["TARDE"], 10), (["TARDE", "UNICA"], 5)])
def test_split_rejects_one_shift_or_tiny_groups(shifts, n):
    with pytest.raises(DataValidationError):
        split_by_shift(_frame(shifts, n), "test")


def test_within_residuals_center_each_shift_and_skip_other_shifts():
    frame = _frame(["MAÑANA", "TARDE", "NOCHE"])
    frame.loc[frame[SHIFT] == "TARDE", list(SCORES)] += 30
    residuals, positions, pooled = within_residuals(frame)
    assert positions.tolist() == list(range(20))
    assert np.allclose(residuals[:10].mean(axis=0), 0) and np.allclose(residuals[10:].mean(axis=0), 0)
    assert pooled.shape == (5, 5) and np.allclose(pooled, residuals.T @ residuals / 18)

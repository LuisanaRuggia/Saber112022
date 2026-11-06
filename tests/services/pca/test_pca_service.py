"""Tests for the PCA service."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from saber11.core.errors.pipeline_errors import DataValidationError
from saber11.models.dataset.dataset_models import SCORES, SHIFT, SHIFTS
from saber11.services.pca.pca_service import run_pca

FIXTURE = Path(__file__).parents[2] / "fixtures" / "muestra_saber11_20224.csv"


@pytest.fixture(scope="module")
def result():
    """Run PCA once on the 2022 sample."""
    data = pd.read_csv(FIXTURE)
    return run_pca(data[data[SHIFT].isin(SHIFTS)].reset_index(drop=True))


def test_pc1_explains_most_variance(result):
    assert result.explained_ratio[0] == pytest.approx(0.765, abs=0.0005)
    assert result.eigenvalues == sorted(result.eigenvalues, reverse=True)
    assert sum(result.eigenvalues) == pytest.approx(len(SCORES))


def test_loadings_shape_and_range(result):
    assert list(result.loadings.index) == list(SCORES)
    assert list(result.loadings.columns) == ["PC1", "PC2", "PC3", "PC4", "PC5"]
    # The published range is reported to two decimals (English is 0.8355 -> 0.84).
    assert result.loadings["PC1"].round(2).between(0.84, 0.91).all()


def test_pc1_means_by_shift(result):
    expected = {"COMPLETA": 1.28, "UNICA": -0.13, "MAÑANA": -0.54, "TARDE": -0.62}
    assert list(result.cp1_means) == list(SHIFTS)
    for shift, value in expected.items():
        assert result.cp1_means[shift] == pytest.approx(value, abs=0.005)


def test_pc1_anova(result):
    assert result.cp1_p < 0.001
    assert 0 < result.cp1_eta_squared < 1


def test_constant_score_raises():
    rng = np.random.default_rng(5)
    frame = pd.DataFrame(rng.normal(50, 10, size=(40, 5)), columns=list(SCORES))
    frame["punt_ingles"] = 50.0
    frame[SHIFT] = np.repeat(["MAÑANA", "TARDE"], 20)
    with pytest.raises(DataValidationError):
        run_pca(frame)

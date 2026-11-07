from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from saber11.models.dataset.dataset_models import NATURE, SCORES, SHIFT, SHIFTS
from saber11.services.assumptions.assumptions_service import check_assumptions
from saber11.services.sensitivity.sensitivity_service import (
    nature_profile, official_only, run_sensitivity, without_outliers)

FIXTURE = Path(__file__).parents[2] / "fixtures" / "muestra_saber11_20224.csv"


def population(n=150, private_boost=10.0, seed=4):
    """Public schools in every shift, plus private schools only in COMPLETA that score higher."""
    rng = np.random.default_rng(seed)
    parts = []
    for shift in SHIFTS:
        for nature, size in (("OFICIAL", n), ("NO OFICIAL", n if shift == "COMPLETA" else 0)):
            block = pd.DataFrame(rng.normal(50, 10, size=(size, len(SCORES))), columns=list(SCORES))
            block += private_boost if nature == "NO OFICIAL" else 0.0
            parts.append(block.assign(**{SHIFT: shift, NATURE: nature}))
    return pd.concat(parts, ignore_index=True)


def test_nature_profile_counts_and_means():
    profile, means = nature_profile(population())
    assert profile.loc["COMPLETA", "share_private"] == pytest.approx(0.5)
    assert profile.loc["TARDE", "n_private"] == 0 and list(profile.index) == list(SHIFTS)
    assert means.loc[("NO OFICIAL", "COMPLETA"), "n"] == 150
    assert means.loc[("NO OFICIAL", "COMPLETA"), "punt_ingles"] > means.loc[("OFICIAL", "COMPLETA"), "punt_ingles"]


def test_official_only_removes_a_nature_driven_shift_effect():
    result = official_only(population(private_boost=15.0), per_group=100, seed=123)
    assert result.official_shifts == list(SHIFTS) and result.n_sample == 400
    assert result.manova.pillai_p > 0.05 and len(result.hotelling) == 6


def test_official_only_skips_shifts_without_enough_public_students():
    frame = population()
    frame = frame[~((frame[SHIFT] != "MAÑANA") & (frame[NATURE] == "OFICIAL"))]
    result = official_only(frame, per_group=100, seed=123)
    assert result.official_shifts == ["MAÑANA"] and result.manova is None and result.hotelling == []


def test_without_outliers_drops_within_shift_outliers():
    sample = pd.read_csv(FIXTURE)
    sample = sample[sample[SHIFT].isin(SHIFTS)].reset_index(drop=True)
    assumptions = check_assumptions(sample)
    result = without_outliers(sample, assumptions)
    assert result.n_removed == assumptions.mahalanobis_within.n_outliers > 0
    from saber11.services.inference.manova_service import run_manova
    # Pillai denominator df is s(N - k - p + s) with s = min(p, k - 1) = 3, so it drops by 3 per row.
    assert result.manova.tests[0].df_den == run_manova(sample).tests[0].df_den - 3 * result.n_removed


def test_run_sensitivity_bundles_both_checks():
    pop = population()
    sample = pop.groupby(SHIFT, group_keys=False).head(60).reset_index(drop=True)
    result = run_sensitivity(sample, pop, check_assumptions(sample), per_group=100, seed=1)
    assert result.official_only.manova is not None and result.without_outliers.manova.pillai >= 0

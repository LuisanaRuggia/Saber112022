import numpy as np
import pandas as pd
import pytest
from scipy import stats

from saber11.models.dataset.dataset_models import SCORES
from saber11.services.spatial.locality_test_service import sample_by_locality, compare_localities

RNG_SEED = 7


def _frame(locality_shift: dict[str, float], n: int, skewed: bool = False) -> pd.DataFrame:
    rng = np.random.default_rng(RNG_SEED)
    parts = []
    for code, shift in locality_shift.items():
        # Exact normal quantiles, shuffled per column: normal by construction, no Shapiro false alarms.
        quantiles = stats.norm.ppf((np.arange(n) + 0.5) / n, loc=50, scale=10)
        normal = np.column_stack([rng.permutation(quantiles) for _ in SCORES])
        base = rng.exponential(10, size=(n, len(SCORES))) if skewed else normal
        part = pd.DataFrame(base + shift, columns=list(SCORES))
        part["cod_localidad"] = code
        parts.append(part)
    return pd.concat(parts, ignore_index=True)


def test_sample_caps_each_locality_and_keeps_small_ones_whole():
    frame = pd.concat([_frame({"01": 0}, 300), _frame({"20": 0}, 82)], ignore_index=True)
    sample = sample_by_locality(frame, per_group=100, seed=123)
    assert sample["cod_localidad"].value_counts().to_dict() == {"01": 100, "20": 82}
    again = sample_by_locality(frame, per_group=100, seed=123)
    pd.testing.assert_frame_equal(sample, again)


def test_normal_data_uses_anova_and_detects_differences():
    result = compare_localities(_frame({"01": 0, "02": 0, "03": 8}, 150), per_group=100, seed=123)
    assert len(result.rows) == 1 + len(SCORES)
    assert result.rows[0].variable == "avg_5"
    for row in result.rows:
        assert row.normal and row.test == "ANOVA" and row.effect_label == "η²"
        assert row.p_bonferroni < 0.001
        assert row.p_bonferroni == pytest.approx(min(1.0, row.p_value * 6))


def test_skewed_data_uses_kruskal_wallis():
    result = compare_localities(_frame({"01": 0, "02": 0}, 150, skewed=True), per_group=100, seed=123)
    for row in result.rows:
        assert not row.normal and row.n_rejected_normality >= 1
        assert row.test == "Kruskal-Wallis" and row.effect_label == "ε²"
        assert 0.0 <= row.effect_size <= 1.0


def test_equal_localities_are_not_significant():
    result = compare_localities(_frame({"01": 0, "02": 0, "03": 0}, 150), per_group=100, seed=123)
    assert all(row.p_bonferroni > 0.05 for row in result.rows)
    assert result.n_sample == 300 and result.n_groups == 3


def test_localities_too_small_for_shapiro_are_dropped():
    frame = pd.concat([_frame({"01": 0, "02": 3}, 120), _frame({"20": 0}, 2)], ignore_index=True)
    result = compare_localities(frame, per_group=100, seed=123)
    assert result.n_groups == 2 and result.excluded == ["20"]


def _scaled(locality_scale: dict[str, float], n: int) -> pd.DataFrame:
    """Normal localities with equal means and different spreads."""
    frame = _frame(dict.fromkeys(locality_scale, 0.0), n)
    for code, scale in locality_scale.items():
        rows = frame["cod_localidad"] == code
        frame.loc[rows, list(SCORES)] = 50 + (frame.loc[rows, list(SCORES)] - 50) * scale
    return frame


def test_normal_but_unequal_variances_use_welch():
    result = compare_localities(_scaled({"01": 0.5, "02": 1.0, "03": 2.5}, 150), per_group=100, seed=123)
    for row in result.rows:
        assert row.normal and row.levene_p < 0.05
        assert row.test == "ANOVA de Welch" and row.effect_label == "η²"


def test_alpha_is_used_and_reported():
    frame = _frame({"01": 0, "02": 0, "03": 0}, 150)
    assert compare_localities(frame, alpha=0.01).alpha == 0.01
    result = compare_localities(_scaled({"01": 0.8, "02": 1.0, "03": 1.25}, 150), alpha=1e-6)
    assert all(row.test == "ANOVA" for row in result.rows)

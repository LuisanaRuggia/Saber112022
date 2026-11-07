"""Compare Bogotá localities: ANOVA (or Welch's ANOVA) when normal, Kruskal-Wallis otherwise."""

import pandas as pd
from scipy import stats

from saber11.models.dataset.dataset_models import SCORES
from saber11.models.spatial.spatial_models import LocalityTestResult, LocalityTestRow

GROUP = "cod_localidad"
MIN_SHAPIRO_N = 3
ANOVA, WELCH, KRUSKAL = "ANOVA", "ANOVA de Welch", "Kruskal-Wallis"


def sample_by_locality(scored: pd.DataFrame, per_group: int, seed: int) -> pd.DataFrame:
    """Draw up to `per_group` students per locality; smaller localities enter whole."""
    parts = [g.sample(n=min(per_group, len(g)), random_state=seed)
             for _, g in scored.groupby(GROUP, sort=True)]
    return pd.concat(parts, ignore_index=True)


def _rejections(groups: list[pd.Series], alpha: float) -> int:
    # Bonferroni across localities: one Shapiro-Wilk test per group.
    threshold = alpha / len(groups)
    return sum(stats.shapiro(g).pvalue < threshold for g in groups)


def _eta_squared(groups: list[pd.Series]) -> float:
    values = pd.concat(groups)
    ss_between = sum(len(g) * (g.mean() - values.mean()) ** 2 for g in groups)
    return float(ss_between / ((values - values.mean()) ** 2).sum())


def _anova(groups: list[pd.Series], equal_var: bool) -> tuple[float, float, float]:
    f, p = stats.f_oneway(*groups, equal_var=equal_var)
    return float(f), float(p), _eta_squared(groups)


def _kruskal(groups: list[pd.Series]) -> tuple[float, float, float]:
    h, p = stats.kruskal(*groups)
    n = sum(len(g) for g in groups)
    return float(h), float(p), float(min(1.0, max(0.0, h / (n - 1))))


def _choose(normal: bool, levene_p: float, alpha: float) -> str:
    """Pick the test: Kruskal-Wallis if not normal, Welch if variances differ, else classic ANOVA."""
    if not normal:
        return KRUSKAL
    return WELCH if levene_p < alpha else ANOVA


def _compare(variable: str, groups: list[pd.Series], alpha: float, n_tests: int) -> LocalityTestRow:
    rejected = _rejections(groups, alpha)
    levene_p = float(stats.levene(*groups).pvalue)
    test = _choose(rejected == 0, levene_p, alpha)
    stat, p, effect = _kruskal(groups) if test == KRUSKAL else _anova(groups, equal_var=test == ANOVA)
    return LocalityTestRow(
        variable=variable, normal=rejected == 0, n_rejected_normality=rejected, levene_p=levene_p,
        test=test, statistic=stat, p_value=p, p_bonferroni=min(1.0, p * n_tests),
        effect_size=effect, effect_label="ε²" if test == KRUSKAL else "η²",
    )


def compare_localities(scored: pd.DataFrame, per_group: int = 100, seed: int = 123,
                       alpha: float = 0.05) -> LocalityTestResult:
    """Test whether localities differ on the 5-score average and on each score."""
    sizes = scored.groupby(GROUP).size()
    excluded = sorted(sizes[sizes < MIN_SHAPIRO_N].index.astype(str))
    kept = scored[~scored[GROUP].isin(excluded)]
    sample = sample_by_locality(kept, per_group, seed).assign(avg_5=lambda d: d[list(SCORES)].mean(axis=1))
    variables = ["avg_5", *SCORES]
    grouped = sample.groupby(GROUP, sort=True)
    rows = [_compare(v, [g[v].reset_index(drop=True) for _, g in grouped], alpha, len(variables))
            for v in variables]
    return LocalityTestResult(rows=rows, per_group=per_group, seed=seed, n_sample=len(sample),
                              n_groups=grouped.ngroups, excluded=excluded, alpha=alpha)

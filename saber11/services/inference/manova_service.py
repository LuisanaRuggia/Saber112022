"""One-way MANOVA of the five scores by shift plus Bonferroni follow-up ANOVAs."""

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.multivariate.manova import MANOVA

from saber11.core.errors.pipeline_errors import DataValidationError
from saber11.models.analysis.analysis_models import AnovaRow, ManovaResult, MultivariateTest
from saber11.models.dataset.dataset_models import SCORES, SHIFT, SHIFTS

TEST_NAMES = ("Pillai's trace", "Wilks' lambda", "Hotelling-Lawley trace", "Roy's greatest root")


def _in_scope(sample: pd.DataFrame) -> pd.DataFrame:
    """Keep compared shifts and validate there are at least two usable groups."""
    frame = sample[sample[SHIFT].isin(SHIFTS)]
    counts = frame[SHIFT].value_counts()
    if len(counts) < 2:
        raise DataValidationError("MANOVA needs at least two shifts")
    if (counts <= len(SCORES)).any():
        raise DataValidationError(f"Every shift needs more than {len(SCORES)} rows: {counts.to_dict()}")
    return frame


def _multivariate_tests(frame: pd.DataFrame) -> list[MultivariateTest]:
    """Fit the statsmodels MANOVA and extract the four classic statistics."""
    formula = f"{' + '.join(SCORES)} ~ C({SHIFT})"
    table = MANOVA.from_formula(formula, data=frame).mv_test().results[f"C({SHIFT})"]["stat"]
    return [
        MultivariateTest(
            name=name,
            value=float(table.loc[name, "Value"]),
            f_value=float(table.loc[name, "F Value"]),
            df_num=float(table.loc[name, "Num DF"]),
            df_den=float(table.loc[name, "Den DF"]),
            p_value=float(table.loc[name, "Pr > F"]),
        )
        for name in TEST_NAMES
    ]


def _anova(frame: pd.DataFrame, score: str, shifts: list[str]) -> AnovaRow:
    """Run a one-way ANOVA of one score by shift with Bonferroni and eta squared."""
    groups = [frame.loc[frame[SHIFT] == shift, score].to_numpy(float) for shift in shifts]
    f_value, p_value = stats.f_oneway(*groups)
    values = np.concatenate(groups)
    ss_total = ((values - values.mean()) ** 2).sum()
    ss_between = sum(len(group) * (group.mean() - values.mean()) ** 2 for group in groups)
    return AnovaRow(
        score=score,
        f_value=float(f_value),
        p_value=float(p_value),
        p_bonferroni=float(min(1.0, p_value * len(SCORES))),
        eta_squared=float(ss_between / ss_total),
    )


def run_manova(sample: pd.DataFrame, alpha: float = 0.05) -> ManovaResult:
    """Test whether the score vector differs by shift; alpha is kept for interface symmetry."""
    frame = _in_scope(sample)
    shifts = [shift for shift in SHIFTS if shift in set(frame[SHIFT])]
    tests = _multivariate_tests(frame)
    pillai = tests[0]
    s = min(len(SCORES), len(shifts) - 1)
    return ManovaResult(
        tests=tests,
        pillai=pillai.value,
        pillai_p=pillai.p_value,
        partial_eta_squared=pillai.value / s,
        anovas=[_anova(frame, score, shifts) for score in SCORES],
    )

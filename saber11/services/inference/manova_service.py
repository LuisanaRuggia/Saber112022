"""One-way MANOVA of the five scores by shift."""

import pandas as pd
from statsmodels.multivariate.manova import MANOVA

from saber11.core.errors.pipeline_errors import DataValidationError
from saber11.models.analysis.analysis_models import ManovaResult, MultivariateTest
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


def run_manova(sample: pd.DataFrame) -> ManovaResult:
    """Test whether the score vector differs by shift."""
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
    )

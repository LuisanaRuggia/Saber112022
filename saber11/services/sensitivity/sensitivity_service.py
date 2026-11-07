"""Robustness checks of the main MANOVA: without outliers and within public schools only.

In Bogotá the full-day shift (Completa) is almost entirely private schools, so a shift effect
can be a school-nature effect. Restricting to public schools separates the two.
"""

import pandas as pd

from saber11.models.analysis.analysis_models import AssumptionsResult
from saber11.models.analysis.sensitivity_models import (
    NatureSensitivity, OutlierSensitivity, SensitivityResult)
from saber11.models.dataset.dataset_models import NATURE, OFFICIAL, SCORES, SHIFT, SHIFTS
from saber11.services.inference.hotelling_service import pairwise_hotelling
from saber11.services.inference.manova_service import run_manova
from saber11.services.ingestion.ingestion_service import draw_sample


def without_outliers(sample: pd.DataFrame, assumptions: AssumptionsResult) -> OutlierSensitivity:
    """Repeat the MANOVA after dropping the within-shift Mahalanobis outliers."""
    positions = assumptions.mahalanobis_within.outlier_index
    kept = sample.drop(index=sample.index[positions])
    return OutlierSensitivity(n_removed=len(positions), manova=run_manova(kept))


def _is_official(frame: pd.DataFrame) -> pd.Series:
    return frame[NATURE].astype("string").str.strip().str.upper().eq(OFFICIAL).fillna(False)


def nature_profile(bogota: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return public/private counts per shift and the score means per (nature, shift)."""
    official = _is_official(bogota)
    profile = pd.DataFrame({"n": bogota.groupby(SHIFT).size(),
                            "n_official": official.groupby(bogota[SHIFT]).sum()}).reindex(SHIFTS).fillna(0)
    profile = profile.astype(int)
    profile["n_private"] = profile["n"] - profile["n_official"]
    profile["share_private"] = profile["n_private"] / profile["n"].where(profile["n"] > 0)
    nature = official.map({True: "OFICIAL", False: "NO OFICIAL"}).rename("naturaleza")
    grouped = bogota.groupby([nature, bogota[SHIFT]])
    means = grouped[list(SCORES)].mean()
    means.insert(0, "n", grouped.size())
    return profile, means


def official_only(bogota: pd.DataFrame, per_group: int, seed: int) -> NatureSensitivity:
    """Sample public-school students per shift and rerun MANOVA and Hotelling on them."""
    profile, means = nature_profile(bogota)
    public = bogota[_is_official(bogota)]
    shifts = [s for s in SHIFTS if profile.loc[s, "n_official"] >= per_group]
    if len(shifts) < 2:
        return NatureSensitivity(profile, means, shifts, 0, None, [])
    sample = draw_sample(public, per_group, seed, shifts)
    return NatureSensitivity(profile, means, shifts, len(sample), run_manova(sample), pairwise_hotelling(sample))


def run_sensitivity(sample: pd.DataFrame, bogota: pd.DataFrame, assumptions: AssumptionsResult,
                    per_group: int, seed: int) -> SensitivityResult:
    """Run every robustness check."""
    return SensitivityResult(without_outliers=without_outliers(sample, assumptions),
                             official_only=official_only(bogota, per_group, seed))

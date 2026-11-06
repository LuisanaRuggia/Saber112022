"""Result contracts for the spatial analysis."""

from dataclasses import dataclass, field

import pandas as pd


@dataclass(frozen=True)
class DepartmentRanking:
    """Department averages ranked by Mathematics + Critical Reading."""

    table: pd.DataFrame   # cols: department, n, <scores>, math_reading, avg_5, rank
    bogota_rank: int | None
    n_departments: int


@dataclass(frozen=True)
class LocalityTestRow:
    """Comparison of localities for one variable, test chosen by normality."""

    variable: str            # "avg_5" or a score column
    normal: bool             # True if no locality rejects Shapiro-Wilk (Bonferroni)
    n_rejected_normality: int
    levene_p: float
    test: str                # "ANOVA" or "Kruskal-Wallis"
    statistic: float
    p_value: float
    p_bonferroni: float
    effect_size: float
    effect_label: str        # "η²" or "ε²"


@dataclass(frozen=True)
class LocalityTestResult:
    """Locality comparison over a stratified sample."""

    rows: list[LocalityTestRow]
    per_group: int
    seed: int
    n_sample: int
    n_groups: int
    excluded: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class LocalityResult:
    """Bogotá results by locality, joined through the DANE code."""

    table: pd.DataFrame   # cols: cod_localidad, localidad, n, <scores>, avg_5 (sorted desc)
    match_rate: float     # share of students with a locality
    n_students: int
    directory_source: str  # URL of the directory resource actually used
    tests: LocalityTestResult | None = None


@dataclass(frozen=True)
class SpatialResult:
    """Department and locality results."""

    departments: DepartmentRanking
    localities: LocalityResult | None

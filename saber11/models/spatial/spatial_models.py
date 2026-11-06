"""Result contracts for the spatial analysis."""

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class DepartmentRanking:
    """Department averages ranked by Mathematics + Critical Reading."""

    table: pd.DataFrame   # cols: department, n, <scores>, math_reading, avg_5, rank
    bogota_rank: int | None
    n_departments: int


@dataclass(frozen=True)
class LocalityResult:
    """Bogotá results by locality, joined through the DANE code."""

    table: pd.DataFrame   # cols: cod_localidad, localidad, n, <scores>, avg_5 (sorted desc)
    match_rate: float     # share of students with a locality
    n_students: int
    directory_source: str  # URL of the directory resource actually used


@dataclass(frozen=True)
class SpatialResult:
    """Department and locality results."""

    departments: DepartmentRanking
    localities: LocalityResult | None

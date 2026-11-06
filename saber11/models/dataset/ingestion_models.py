"""Result contract of the ingestion stage."""

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class IngestionResult:
    """Clean Bogotá population, its sample and national department means."""

    bogota: pd.DataFrame       # STUDENT_COLUMNS, shifts in SHIFTS, numeric scores, no NA
    sample: pd.DataFrame       # stratified sample drawn from `bogota`
    departments: pd.DataFrame  # cols: department, n, <SCORES> (means), one row per department
    source_detail: str         # human-readable provenance (URL or file name + period)

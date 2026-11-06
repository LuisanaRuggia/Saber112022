"""Build the clean Bogotá population, its stratified sample and department means."""

import pandas as pd

from saber11.configs.pipeline.pipeline_config import PipelineConfig
from saber11.core.errors.pipeline_errors import DataValidationError
from saber11.models.dataset.dataset_models import DEPARTMENT, SCORES, SHIFT, SHIFTS, STUDENT_COLUMNS
from saber11.models.dataset.ingestion_models import IngestionResult
from saber11.repositories.dataicfes.dataicfes_repository import DataIcfesRepository
from saber11.repositories.socrata.socrata_repository import SocrataRepository


def clean_students(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize shift, keep study shifts, coerce scores and drop rows without scores."""
    out = df.copy()
    out[SHIFT] = out[SHIFT].astype("string").str.strip().str.upper()
    out = out[out[SHIFT].isin(SHIFTS)].copy()
    out[SHIFT] = out[SHIFT].astype(object)
    out[list(SCORES)] = out[list(SCORES)].apply(pd.to_numeric, errors="coerce")
    return out.dropna(subset=list(SCORES))[list(STUDENT_COLUMNS)].reset_index(drop=True)


def is_bogota(series: pd.Series) -> pd.Series:
    """Return a mask of values naming Bogotá, ignoring accents and case."""
    text = series.fillna("").astype(str).str.normalize("NFKD").str.upper()
    return text.str.contains("BOGOT", regex=False)


def department_means(national: pd.DataFrame) -> pd.DataFrame:
    """Return n and mean scores per department from student rows."""
    scores = national[list(SCORES)].apply(pd.to_numeric, errors="coerce")
    grouped = scores.groupby(national[DEPARTMENT].values)
    out = grouped.mean()
    out.insert(0, "n", grouped.size())
    out.index.name = "department"
    return out.reset_index()


def draw_sample(bogota: pd.DataFrame, per_group: int, seed: int) -> pd.DataFrame:
    """Draw per_group students from each shift, reproducibly."""
    parts = []
    for shift in SHIFTS:
        group = bogota[bogota[SHIFT] == shift]
        if len(group) < per_group:
            raise DataValidationError(
                f"shift {shift} has {len(group)} students, fewer than the {per_group} required")
        parts.append(group.sample(n=per_group, random_state=seed))
    return pd.concat(parts).reset_index(drop=True)


def _require_students(bogota: pd.DataFrame, period: str) -> None:
    if bogota.empty:
        raise DataValidationError(f"no valid Bogotá students found for period {period}")


def ingest(config: PipelineConfig, socrata: SocrataRepository | None = None,
           dataicfes_factory=DataIcfesRepository) -> IngestionResult:
    """Load the configured source and return population, sample and department means."""
    if config.source == "api":
        socrata = socrata or SocrataRepository(app_token=config.socrata_app_token)
        raw = socrata.fetch_bogota(config.period)
        departments = socrata.fetch_department_means(config.period)
        detail = f"API de datos.gov.co (dataset kgxf-xxbe), periodo {config.period}"
    else:
        national = dataicfes_factory(config.dataicfes_path).read(config.period)
        raw = national[is_bogota(national[DEPARTMENT])]
        departments = department_means(national)
        detail = f"archivo DataIcfes {config.dataicfes_path.name}, periodo {config.period}"
    bogota = clean_students(raw)
    _require_students(bogota, config.period)
    sample = draw_sample(bogota, config.sample_per_group, config.seed)
    return IngestionResult(bogota=bogota, sample=sample, departments=departments, source_detail=detail)

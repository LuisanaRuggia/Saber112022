"""Department ranking and Bogotá locality results."""

import pandas as pd

from saber11.core.errors.pipeline_errors import SourceUnavailableError
from saber11.models.dataset.dataset_models import DANE_SCHOOL, DANE_SITE, LOCALITIES, SCORES
from saber11.models.spatial.spatial_models import DepartmentRanking, LocalityResult, SpatialResult
from saber11.repositories.directory.school_directory_repository import SchoolDirectoryRepository
from saber11.services.ingestion.ingestion_service import is_bogota
from saber11.services.spatial.locality_test_service import compare_localities

MIN_N = 30


def rank_departments(departments: pd.DataFrame) -> DepartmentRanking:
    """Rank departments (n >= 30) by Mathematics + Critical Reading, 1 = best."""
    t = departments[departments["n"] >= MIN_N].copy()
    t["math_reading"] = t["punt_matematicas"] + t["punt_lectura_critica"]
    t["avg_5"] = t[list(SCORES)].mean(axis=1)
    t = t.sort_values("math_reading", ascending=False).reset_index(drop=True)
    t["rank"] = t["math_reading"].rank(method="min", ascending=False).astype(int)
    mask = is_bogota(t["department"])
    bogota_rank = int(t.loc[mask, "rank"].min()) if mask.any() else None
    return DepartmentRanking(table=t, bogota_rank=bogota_rank, n_departments=len(t))


def _digits(series: pd.Series) -> pd.Series:
    text = series.astype("string").str.strip().str.replace(r"\.0$", "", regex=True)
    return text.str.replace(r"\D", "", regex=True)


def _lookup(directory: pd.DataFrame, key: str) -> dict:
    d = pd.DataFrame({"k": _digits(directory[key]), "loc": directory["cod_localidad"].astype("string")})
    d = d[(d["k"] != "") & d["loc"].notna() & (d["loc"] != "")]
    return d.drop_duplicates("k").set_index("k")["loc"].to_dict()


def _assign_locality(bogota: pd.DataFrame, directory: pd.DataFrame) -> pd.Series:
    by_site = _digits(bogota[DANE_SITE]).map(_lookup(directory, "dane_sede"))
    by_school = _digits(bogota[DANE_SCHOOL]).map(_lookup(directory, "dane_est"))
    return by_site.fillna(by_school)


def locality_results(bogota: pd.DataFrame, directory: pd.DataFrame, directory_source: str,
                     per_group: int = 100, seed: int = 123) -> LocalityResult:
    """Join students to localities through DANE codes and summarize each locality."""
    codes = _assign_locality(bogota, directory)
    scored = bogota[list(SCORES)].assign(cod_localidad=codes.values).dropna(subset=["cod_localidad"])
    grouped = scored.groupby("cod_localidad")
    t = grouped[list(SCORES)].mean().round(2)
    t.insert(0, "n", grouped.size())
    t["avg_5"] = t[list(SCORES)].mean(axis=1).round(2)
    t = t.reset_index()
    t.insert(1, "localidad", t["cod_localidad"].map(LOCALITIES).fillna(t["cod_localidad"]))
    t = t.sort_values("avg_5", ascending=False).reset_index(drop=True)
    n = len(bogota)
    tests = compare_localities(scored, per_group, seed) if t["n"].ge(3).sum() >= 2 else None
    return LocalityResult(table=t, match_rate=len(scored) / n if n else 0.0,
                          n_students=n, directory_source=directory_source, tests=tests)


def build_spatial(departments: pd.DataFrame, bogota: pd.DataFrame,
                  directory_repo: SchoolDirectoryRepository | None,
                  per_group: int = 100, seed: int = 123) -> SpatialResult:
    """Rank departments and, if the directory is reachable, summarize localities."""
    ranking = rank_departments(departments)
    try:
        directory, source = (directory_repo or SchoolDirectoryRepository()).fetch()
    except SourceUnavailableError:
        return SpatialResult(departments=ranking, localities=None)
    return SpatialResult(departments=ranking, localities=locality_results(bogota, directory, source, per_group, seed))

"""Reader for the Saber 11 dataset on datos.gov.co (Socrata SODA API)."""

import time

import pandas as pd
import requests

from saber11.core.errors.pipeline_errors import SourceUnavailableError
from saber11.models.dataset.dataset_models import (
    DEPARTMENT, PERIOD, SCORES, SHIFT, SHIFTS, STUDENT_COLUMNS, STUDENT_ID)

BASE_URL = "https://www.datos.gov.co/resource/kgxf-xxbe.json"
RETRY_STATUS = {429}


class SocrataRepository:
    """Fetch Bogotá students and department means from Socrata."""

    def __init__(self, session=None, app_token=None, page_size=50000, max_retries=5,
                 sleep=time.sleep, base_url=BASE_URL, timeout=120):
        self.session = session or requests.Session()
        self.app_token = app_token
        self.page_size = page_size
        self.max_retries = max_retries
        self.sleep = sleep
        self.base_url = base_url
        self.timeout = timeout

    def _headers(self) -> dict:
        return {"X-App-Token": self.app_token} if self.app_token else {}

    def _get(self, params: dict) -> list[dict]:
        """GET one page, retrying 429/5xx/network errors with exponential backoff."""
        last = "unknown error"
        for attempt in range(self.max_retries):
            if attempt:
                self.sleep(2 ** (attempt - 1))
            try:
                resp = self.session.get(self.base_url, params=params,
                                        headers=self._headers(), timeout=self.timeout)
            except requests.RequestException as exc:
                last = f"{type(exc).__name__}: {exc}"
                continue
            if resp.status_code == 200:
                try:
                    return resp.json()
                except ValueError:
                    last = "HTTP 200 with a body that is not JSON"
                    continue
            last = f"HTTP {resp.status_code}"
            if resp.status_code not in RETRY_STATUS and resp.status_code < 500:
                break
        raise SourceUnavailableError(f"Socrata request failed after retries: {last}")

    def fetch_bogota(self, period: str) -> pd.DataFrame:
        """Return every Bogotá student of the period with STUDENT_COLUMNS."""
        where = f"{PERIOD}='{period}' AND upper({DEPARTMENT}) like '%BOGOT%'"
        rows: list[dict] = []
        offset = 0
        while True:
            page = self._get({"$select": ",".join(STUDENT_COLUMNS), "$where": where,
                              "$order": ":id", "$limit": self.page_size, "$offset": offset})
            if not page:
                break
            rows.extend(page)
            offset += self.page_size
        return pd.DataFrame(rows).reindex(columns=list(STUDENT_COLUMNS))

    def fetch_department_means(self, period: str) -> pd.DataFrame:
        """Return unique students and mean scores per department, filtered like the Bogotá population.

        The dataset repeats most students as identical rows. `n` counts distinct student ids;
        the means are computed over rows, which equals the per-student mean when copies are exact.
        """
        # Aliases must differ from column names because WHERE also filters on the scores.
        means = ", ".join(f"avg({c}::number) AS mean_{c}" for c in SCORES)
        shifts = ", ".join(f"'{s}'" for s in SHIFTS)
        scored = " AND ".join(f"{c} IS NOT NULL" for c in SCORES)
        where = f"{PERIOD}='{period}' AND upper({SHIFT}) IN ({shifts}) AND {scored}"
        page = self._get({"$select": f"{DEPARTMENT}, count(distinct {STUDENT_ID}) AS n, {means}",
                          "$where": where, "$group": DEPARTMENT, "$limit": 100})
        renames = {DEPARTMENT: "department", **{f"mean_{c}": c for c in SCORES}}
        df = pd.DataFrame(page).rename(columns=renames)
        df = df.reindex(columns=["department", "n", *SCORES])
        df[["n", *SCORES]] = df[["n", *SCORES]].apply(pd.to_numeric, errors="coerce")
        return df

"""Reader for the SED school directory of Bogotá (CKAN, latest GeoJSON resource)."""

import json
from pathlib import Path

import pandas as pd
import requests

from saber11.core.errors.pipeline_errors import DataValidationError, SourceUnavailableError
from saber11.core.formatting.dane_codes import digits

PACKAGE_URL = "https://datosabiertos.bogota.gov.co/api/3/action/package_show"
PACKAGE_ID = "colegios-bogota-d-c"


class SchoolDirectoryRepository:
    """Fetch school DANE codes with their locality code."""

    def __init__(self, session=None, timeout=120, local_path: Path | None = None):
        self.session = session or requests.Session()
        self.timeout = timeout
        self.local_path = local_path

    def _json(self, url: str, params=None):
        try:
            resp = self.session.get(url, params=params, headers={}, timeout=self.timeout)
            if resp.status_code != 200:
                raise SourceUnavailableError(f"{url} answered HTTP {resp.status_code}")
            return resp.json()
        except requests.RequestException as exc:
            raise SourceUnavailableError(f"{url} unreachable: {exc}") from exc
        except ValueError as exc:
            raise SourceUnavailableError(f"{url} answered a body that is not JSON") from exc

    def _latest_geojson(self) -> str:
        resources = self._json(PACKAGE_URL, {"id": PACKAGE_ID})["result"]["resources"]
        geo = [r for r in resources if str(r.get("format", "")).lower() == "geojson"]
        if not geo:
            raise SourceUnavailableError("no GeoJSON resource in the school directory")
        key = lambda r: str(r.get("last_modified") or r.get("created") or "")
        return max(geo, key=key)["url"]

    def fetch(self) -> tuple[pd.DataFrame, str]:
        """Return (dane_sede, dane_est, cod_localidad) and the URL used."""
        if self.local_path is not None:
            url = str(self.local_path)
            try:
                data = json.loads(Path(self.local_path).read_text(encoding="utf-8"))
            except ValueError as exc:
                raise DataValidationError(f"{self.local_path} is not a valid GeoJSON file") from exc
        else:
            url = self._latest_geojson()
            data = self._json(url)
        rows = []
        for feature in data.get("features", []):
            p = feature.get("properties") or {}
            loc = digits(p.get("COD_LOCA"))
            rows.append({"dane_sede": digits(p.get("DANE12_SED")),
                         "dane_est": digits(p.get("DANE12_EST")),
                         "cod_localidad": loc.zfill(2) if loc else ""})
        return pd.DataFrame(rows, columns=["dane_sede", "dane_est", "cod_localidad"]), url

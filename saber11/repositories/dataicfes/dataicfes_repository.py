"""Chunked reader for DataIcfes flat files and datos.gov.co CSV exports."""

from pathlib import Path

import pandas as pd

from saber11.core.errors.pipeline_errors import DataValidationError
from saber11.models.dataset.dataset_models import PERIOD, STUDENT_COLUMNS

DELIMITERS = ("¬", "|", ";", ",")
ALIASES = {"punt_sociales": "punt_sociales_ciudadanas", "punt_lectura": "punt_lectura_critica"}


def _canonical(name: str) -> str:
    key = name.strip().strip('"').lower()
    return ALIASES.get(key, key)


class DataIcfesRepository:
    """Read national rows of one period from a local flat file."""

    def __init__(self, path, chunksize: int = 200_000):
        self.path = Path(path)
        self.chunksize = chunksize

    def _header(self) -> tuple[str, str]:
        """Return the raw header line and the delimiter that splits it best."""
        with self.path.open(encoding="utf-8-sig") as fh:
            line = fh.readline().rstrip("\r\n")
        return line, max(DELIMITERS, key=line.count)

    def read(self, period: str) -> pd.DataFrame:
        """Return rows of the period with STUDENT_COLUMNS in lowercase."""
        line, sep = self._header()
        raw = [c.strip().strip('"') for c in line.split(sep)]
        found = {_canonical(c): c for c in raw}
        missing = [c for c in STUDENT_COLUMNS if c not in found]
        if missing:
            raise DataValidationError(f"{self.path.name} lacks columns: {missing}")
        wanted = {found[c] for c in STUDENT_COLUMNS}
        chunks = []
        reader = pd.read_csv(self.path, sep=sep, usecols=lambda c: c.strip() in wanted,
                             dtype=str, chunksize=self.chunksize, encoding="utf-8-sig",
                             engine="python" if sep == "¬" else "c")
        for chunk in reader:
            chunk.columns = [_canonical(c) for c in chunk.columns]
            chunk = chunk[chunk[PERIOD].str.strip() == period]
            chunks.append(chunk[list(STUDENT_COLUMNS)])
        if not chunks:
            return pd.DataFrame(columns=list(STUDENT_COLUMNS))
        return pd.concat(chunks, ignore_index=True)

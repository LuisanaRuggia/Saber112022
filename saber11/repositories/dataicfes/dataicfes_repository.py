"""Chunked reader for DataIcfes flat files and datos.gov.co CSV exports."""

import codecs
import io
from pathlib import Path

import pandas as pd

from saber11.core.errors.pipeline_errors import DataValidationError
from saber11.models.dataset.dataset_models import PERIOD, STUDENT_COLUMNS

DELIMITERS = ("¬", "|", ";", ",")
ALIASES = {"punt_sociales": "punt_sociales_ciudadanas", "punt_lectura": "punt_lectura_critica"}
SNIFF_BYTES = 4 * 1024 * 1024
# The C parser only takes single-byte separators; '¬' is two bytes in UTF-8, so it is
# swapped for the ASCII unit separator on the fly instead of using the slow Python parser.
UNIT_SEPARATOR = "\x1f"


def _canonical(name: str) -> str:
    key = name.strip().strip('"').lower()
    return ALIASES.get(key, key)


def sniff_encoding(path: Path) -> str:
    """Return 'utf-8-sig' when the first megabytes decode as UTF-8, else 'latin-1'."""
    with path.open("rb") as fh:
        head = fh.read(SNIFF_BYTES)
    try:
        codecs.getincrementaldecoder("utf-8")().decode(head, final=False)
    except UnicodeDecodeError:
        return "latin-1"
    return "utf-8-sig"


class _Translated(io.TextIOBase):
    """Text stream that replaces one character with another while reading."""

    def __init__(self, handle, old: str, new: str):
        self._handle, self._old, self._new = handle, old, new

    def readable(self) -> bool:
        return True

    def read(self, size: int = -1) -> str:
        return self._handle.read(size).replace(self._old, self._new)


class DataIcfesRepository:
    """Read national rows of one period from a local flat file."""

    def __init__(self, path, chunksize: int = 200_000, encoding: str | None = None):
        self.path = Path(path)
        self.chunksize = chunksize
        self.encoding = encoding or sniff_encoding(self.path)

    def _header(self) -> tuple[str, str]:
        """Return the raw header line and the delimiter that splits it best."""
        with self.path.open(encoding=self.encoding) as fh:
            line = fh.readline().rstrip("\r\n")
        return line, max(DELIMITERS, key=line.count)

    def _columns(self, line: str, sep: str) -> set[str]:
        """Return the raw names of the required columns, or raise if any is missing."""
        found = {_canonical(c): c.strip().strip('"') for c in line.split(sep)}
        missing = [c for c in STUDENT_COLUMNS if c not in found]
        if missing:
            raise DataValidationError(f"{self.path.name} lacks columns: {missing}")
        return {found[c] for c in STUDENT_COLUMNS}

    def read(self, period: str) -> pd.DataFrame:
        """Return rows of the period with STUDENT_COLUMNS in lowercase."""
        try:
            line, sep = self._header()
            wanted = self._columns(line, sep)
            with self.path.open(encoding=self.encoding, newline="") as fh:
                return self._filter(fh, sep, wanted, period)
        except UnicodeDecodeError as exc:
            raise DataValidationError(
                f"{self.path.name} is not valid {self.encoding}; set SABER11_DATAICFES_ENCODING") from exc

    def _filter(self, fh, sep: str, wanted: set[str], period: str) -> pd.DataFrame:
        source = _Translated(fh, sep, UNIT_SEPARATOR) if len(sep.encode("utf-8")) > 1 else fh
        reader = pd.read_csv(source, sep=UNIT_SEPARATOR if source is not fh else sep,
                             usecols=lambda c: c.strip() in wanted, dtype=str, chunksize=self.chunksize)
        chunks = []
        for chunk in reader:
            chunk.columns = [_canonical(c) for c in chunk.columns]
            chunk = chunk[chunk[PERIOD].str.strip() == period]
            chunks.append(chunk[list(STUDENT_COLUMNS)])
        if not chunks:
            return pd.DataFrame(columns=list(STUDENT_COLUMNS))
        return pd.concat(chunks, ignore_index=True)

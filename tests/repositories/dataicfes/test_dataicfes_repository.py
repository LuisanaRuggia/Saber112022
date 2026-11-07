from pathlib import Path

import pytest

from saber11.core.errors.pipeline_errors import DataValidationError
from saber11.models.dataset.dataset_models import STUDENT_COLUMNS
from saber11.repositories.dataicfes.dataicfes_repository import DataIcfesRepository

FIXTURE = Path(__file__).parents[2] / "fixtures" / "saber11_head.csv"
HEADER = ["PERIODO", "ESTU_CONSECUTIVO", "COLE_DEPTO_UBICACION", "COLE_JORNADA", "COLE_COD_DANE_SEDE",
          "COLE_COD_DANE_ESTABLECIMIENTO", "COLE_NATURALEZA", "PUNT_MATEMATICAS",
          "PUNT_LECTURA_CRITICA", "PUNT_C_NATURALES", "PUNT_SOCIALES_CIUDADANAS", "PUNT_INGLES"]
ROWS = [["20251", "SB1", "BOGOTÁ", "MAÑANA", "111001000012", "111001000012", "OFICIAL", "50", "60", "55", "52", "48"],
        ["20252", "SB2", "ANTIOQUIA", "TARDE", "005001000001", "005001000001", "NO OFICIAL", "70", "65", "60", "58", "66"]]


def write(tmp_path, sep, header=HEADER, rows=ROWS, encoding="utf-8"):
    path = tmp_path / "f.txt"
    path.write_text("\n".join(sep.join(r) for r in [header, *rows]), encoding=encoding)
    return path


@pytest.mark.parametrize("sep", ["¬", "|", ";", ","])
def test_sniffs_delimiter_and_filters_period(tmp_path, sep):
    df = DataIcfesRepository(write(tmp_path, sep)).read("20251")
    assert list(df.columns) == list(STUDENT_COLUMNS) and len(df) == 1
    assert df["cole_cod_dane_sede"].iloc[0] == "111001000012"
    assert df["punt_matematicas"].iloc[0] == "50"


def test_reads_in_chunks(tmp_path):
    rows = [ROWS[0]] * 5 + [ROWS[1]] * 3
    df = DataIcfesRepository(write(tmp_path, "|", rows=rows), chunksize=2).read("20251")
    assert len(df) == 5


def test_accepts_aliases(tmp_path):
    header = [h.replace("_LECTURA_CRITICA", "_LECTURA").replace("_SOCIALES_CIUDADANAS", "_SOCIALES")
              for h in HEADER]
    df = DataIcfesRepository(write(tmp_path, ";", header=header)).read("20252")
    assert df["punt_lectura_critica"].iloc[0] == "65" and len(df) == 1


def test_missing_required_column_raises(tmp_path):
    header = [h for h in HEADER if h != "PUNT_INGLES"]
    rows = [r[:-1] for r in ROWS]
    with pytest.raises(DataValidationError):
        DataIcfesRepository(write(tmp_path, "|", header=header, rows=rows)).read("20251")


def test_quoted_csv_fixture_from_datos_gov():
    df = DataIcfesRepository(FIXTURE).read("20194")
    assert len(df) == 342 and list(df.columns) == list(STUDENT_COLUMNS)
    assert (df["periodo"] == "20194").all()


@pytest.mark.parametrize("sep", ["¬", "|"])
def test_latin1_files_are_detected(tmp_path, sep):
    repo = DataIcfesRepository(write(tmp_path, sep, encoding="latin-1"))
    df = repo.read("20251")
    assert repo.encoding == "latin-1" and df["cole_jornada"].iloc[0] == "MAÑANA"
    assert df["cole_depto_ubicacion"].iloc[0] == "BOGOTÁ"


def test_utf8_is_detected_and_keeps_accents(tmp_path):
    repo = DataIcfesRepository(write(tmp_path, "¬"))
    assert repo.encoding == "utf-8-sig" and repo.read("20251")["cole_jornada"].iloc[0] == "MAÑANA"


def test_wrong_explicit_encoding_raises_validation_error(tmp_path):
    with pytest.raises(DataValidationError, match="SABER11_DATAICFES_ENCODING"):
        DataIcfesRepository(write(tmp_path, "|", encoding="latin-1"), encoding="utf-8").read("20251")


def test_unit_separator_swap_keeps_values_with_accents(tmp_path):
    rows = [ROWS[0][:2] + ["SAN ANDRÉS ì"] + ROWS[0][3:]]
    df = DataIcfesRepository(write(tmp_path, "¬", rows=rows), chunksize=1).read("20251")
    assert df["cole_depto_ubicacion"].iloc[0] == "SAN ANDRÉS ì" and df["punt_ingles"].iloc[0] == "48"

"""Normalize DANE school codes that arrive as text, integers or floats ('111001000012.0')."""

import re

import pandas as pd


def digits(value) -> str:
    """Return only the digits of one code, dropping a trailing '.0'; '' for missing values."""
    if value is None or (isinstance(value, float) and value != value):
        return ""
    return re.sub(r"\D", "", re.sub(r"\.0$", "", str(value).strip()))


def digits_series(series: pd.Series) -> pd.Series:
    """Vectorized `digits` for a whole column."""
    text = series.astype("string").str.strip().str.replace(r"\.0$", "", regex=True)
    return text.str.replace(r"\D", "", regex=True)

"""Convert PipelineResults into JSON-serializable structures."""

import dataclasses
from typing import Any

import numpy as np
import pandas as pd


def to_jsonable(value: Any) -> Any:
    """Recursively convert dataclasses, pandas and numpy objects to plain Python."""
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {f.name: to_jsonable(getattr(value, f.name)) for f in dataclasses.fields(value)}
    if isinstance(value, pd.DataFrame):
        return json_records(value)
    if isinstance(value, pd.Series):
        return {str(k): to_jsonable(v) for k, v in value.items()}
    if isinstance(value, dict):
        return {str(k): to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(v) for v in value]
    if isinstance(value, np.generic):
        return to_jsonable(value.item())
    if isinstance(value, float) and not np.isfinite(value):
        return None
    return value


def json_records(frame: pd.DataFrame) -> list[dict]:
    """Return DataFrame rows as dicts keyed by the index when it is meaningful."""
    keep_index = not isinstance(frame.index, pd.RangeIndex)
    data = frame.reset_index() if keep_index else frame
    return [{str(k): to_jsonable(v) for k, v in row.items()} for row in data.to_dict(orient="records")]

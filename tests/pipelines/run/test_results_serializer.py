import json

import numpy as np
import pandas as pd

from saber11.pipelines.run.results_serializer import to_jsonable
from tests.fakes.results_factory import build_results


def test_full_results_are_json_serializable():
    text = json.dumps(to_jsonable(build_results()), ensure_ascii=False)
    assert "Pillai" in text and "BOGOTÁ" in text


def test_numpy_nan_and_frames():
    out = to_jsonable({"a": np.float64(1.5), "b": float("nan"), "c": pd.DataFrame({"x": [1]}, index=["r"])})
    assert out == {"a": 1.5, "b": None, "c": [{"index": "r", "x": 1}]}

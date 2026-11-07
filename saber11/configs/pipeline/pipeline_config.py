"""Typed pipeline settings parsed once from the environment."""

import codecs
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from saber11.core.errors.pipeline_errors import ConfigError

SOURCES = ("api", "dataicfes")


@dataclass(frozen=True)
class PipelineConfig:
    """Validated settings for one pipeline run."""

    source: str = "api"
    period: str = "20224"
    dataicfes_path: Path | None = None
    dataicfes_encoding: str | None = None  # None: detect UTF-8, else Latin-1
    sample_per_group: int = 100
    seed: int = 123
    output_dir: Path = Path("output")
    socrata_app_token: str | None = None
    directory_path: Path | None = None
    alpha: float = 0.05

    @property
    def run_dir(self) -> Path:
        """Return the output folder for this period."""
        return self.output_dir / self.period


def _int(env: Mapping[str, str], key: str, default: int) -> int:
    raw = env.get(key, str(default))
    try:
        value = int(raw)
    except ValueError as exc:
        raise ConfigError(f"{key} must be an integer, got {raw!r}") from exc
    if value <= 0:
        raise ConfigError(f"{key} must be positive")
    return value


def _encoding(name: str | None) -> str | None:
    """Return the encoding name if Python knows it; None means auto-detect."""
    if name is None:
        return None
    try:
        codecs.lookup(name)
    except LookupError as exc:
        raise ConfigError(f"SABER11_DATAICFES_ENCODING {name!r} is not a known encoding") from exc
    return name


def load_config(env: Mapping[str, str] | None = None) -> PipelineConfig:
    """Build and validate the config from environment variables."""
    env = os.environ if env is None else env
    source = env.get("SABER11_SOURCE", "api").strip().lower()
    if source not in SOURCES:
        raise ConfigError(f"SABER11_SOURCE must be one of {SOURCES}")
    raw_path = env.get("SABER11_DATAICFES_PATH")
    path = Path(raw_path) if raw_path else None
    if source == "dataicfes" and (path is None or not path.is_file()):
        raise ConfigError("SABER11_DATAICFES_PATH must point to an existing file")
    encoding = _encoding(env.get("SABER11_DATAICFES_ENCODING", "").strip() or None)
    raw_dir = env.get("SABER11_DIRECTORY_PATH")
    directory = Path(raw_dir) if raw_dir else None
    if directory is not None and not directory.is_file():
        raise ConfigError("SABER11_DIRECTORY_PATH must point to an existing file")
    period = env.get("SABER11_PERIOD", "20224").strip()
    if not (period.isdigit() and len(period) == 5):
        raise ConfigError("SABER11_PERIOD must look like 20224 (year + semester)")
    return PipelineConfig(
        source=source,
        period=period,
        dataicfes_path=path,
        dataicfes_encoding=encoding,
        sample_per_group=_int(env, "SABER11_SAMPLE_PER_GROUP", 100),
        seed=_int(env, "SABER11_SEED", 123),
        output_dir=Path(env.get("SABER11_OUTPUT_DIR", "output")),
        socrata_app_token=env.get("SOCRATA_APP_TOKEN") or None,
        directory_path=directory,
    )

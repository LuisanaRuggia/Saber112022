"""Files produced by one pipeline run."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RunArtifacts:
    """Paths of the outputs written by a run."""

    run_dir: Path
    pdf: Path
    results_json: Path
    sample_csv: Path
    shift_summary_csv: Path
    departments_csv: Path
    localities_csv: Path | None

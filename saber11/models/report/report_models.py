"""Aggregate of every result the report needs."""

from dataclasses import dataclass, field

from saber11.models.analysis.analysis_models import (
    AssumptionsResult,
    DescriptiveResult,
    HotellingPair,
    ManovaResult,
    PcaResult,
)
from saber11.models.spatial.spatial_models import SpatialResult


@dataclass(frozen=True)
class RunMetadata:
    """Provenance of one pipeline run."""

    period: str
    source: str
    source_detail: str
    population_size: int
    sample_per_group: int
    seed: int
    alpha: float
    generated_at: str


@dataclass(frozen=True)
class Conclusions:
    """Narrative findings derived from the numbers."""

    headline: str
    findings: list[str] = field(default_factory=list)
    caveats: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class PipelineResults:
    """Everything produced by one run."""

    metadata: RunMetadata
    descriptive: DescriptiveResult
    assumptions: AssumptionsResult
    manova: ManovaResult
    hotelling: list[HotellingPair]
    pca: PcaResult
    spatial: SpatialResult
    conclusions: Conclusions

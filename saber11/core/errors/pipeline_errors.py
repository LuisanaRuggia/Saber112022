"""Single error contract for the pipeline."""


class PipelineError(Exception):
    """Base error carrying a machine-readable code."""

    code = "pipeline_error"

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class ConfigError(PipelineError):
    """Raise when configuration is missing or invalid."""

    code = "config_invalid"


class SourceUnavailableError(PipelineError):
    """Raise when an external data source cannot be reached after retries."""

    code = "source_unavailable"


class DataValidationError(PipelineError):
    """Raise when input data does not meet the analysis contract."""

    code = "data_invalid"

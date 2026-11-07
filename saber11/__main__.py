"""CLI entry point: python -m saber11 run.

stdout carries only the path of the PDF, so scripts can capture it; progress and errors go to stderr.
"""

import argparse
import logging
import os
import sys

from saber11.configs.pipeline.pipeline_config import load_config
from saber11.core.errors.pipeline_errors import PipelineError

log = logging.getLogger("saber11")
DEBUG_ENV = "SABER11_DEBUG"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="saber11",
                                     description="Saber 11 Bogotá pipeline: MANOVA, PCA and PDF report.")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("run", help="run the full pipeline and write CSV, JSON and PDF outputs")
    return parser


def _configure_logging() -> None:
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter("%(message)s"))
    log.handlers[:] = [handler]
    log.setLevel(logging.INFO)
    log.propagate = False


def main(argv: list[str] | None = None, *, run_fn=None) -> int:
    """Run the CLI and return the process exit code."""
    args = _parser().parse_args(argv)
    if args.command != "run":
        _parser().print_help()
        return 0
    _configure_logging()
    try:
        if run_fn is None:
            from saber11.pipelines.run.run_pipeline import run as run_fn
        artifacts = run_fn(load_config())
    except PipelineError as exc:
        print(f"error {exc.code}: {exc.message}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        if os.environ.get(DEBUG_ENV):
            log.exception("unexpected failure")
        print(f"error internal: unexpected {type(exc).__name__}; rerun with {DEBUG_ENV}=1 for the traceback",
              file=sys.stderr)
        return 2
    print(artifacts.pdf)
    return 0


if __name__ == "__main__":
    sys.exit(main())

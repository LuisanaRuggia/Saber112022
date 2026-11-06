"""CLI entry point: python -m saber11 run."""

import argparse
import json
import logging
import sys

from saber11.configs.pipeline.pipeline_config import load_config
from saber11.core.errors.pipeline_errors import PipelineError

log = logging.getLogger("saber11")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="saber11", description="Saber 11 Bogotá pipeline: MANOVA, PCA and PDF report.")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("run", help="run the full pipeline and write CSV, JSON and PDF outputs")
    return parser


def main(argv: list[str] | None = None, *, run_fn=None) -> int:
    """Run the CLI and return the process exit code."""
    args = _parser().parse_args(argv)
    if args.command != "run":
        _parser().print_help()
        return 0
    try:
        if run_fn is None:
            from saber11.pipelines.run.run_pipeline import run as run_fn
        artifacts = run_fn(load_config())
    except PipelineError as exc:
        print(f"error {exc.code}: {exc.message}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({"level": "error", "event": "unexpected", "detail": repr(exc)}), flush=True)
        log.exception("unexpected failure")
        print("error internal: unexpected failure, see logs", file=sys.stderr)
        return 2
    print(artifacts.pdf)
    return 0


if __name__ == "__main__":
    sys.exit(main())

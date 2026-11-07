from pathlib import Path
from types import SimpleNamespace

import pytest

from saber11.__main__ import main
from saber11.core.errors.pipeline_errors import SourceUnavailableError


def test_run_prints_pdf_path(capsys):
    code = main(["run"], run_fn=lambda cfg: SimpleNamespace(pdf=Path("out/x.pdf")))
    assert code == 0 and "out/x.pdf" in capsys.readouterr().out


def test_pipeline_error_exits_1(capsys):
    def boom(cfg):
        raise SourceUnavailableError("socrata down")
    assert main(["run"], run_fn=boom) == 1
    assert "error source_unavailable: socrata down" in capsys.readouterr().err


def test_unexpected_error_exits_2_without_traceback(capsys, monkeypatch):
    monkeypatch.delenv("SABER11_DEBUG", raising=False)
    def boom(cfg):
        raise ValueError("secret detail")
    assert main(["run"], run_fn=boom) == 2
    out, err = capsys.readouterr()
    assert "Traceback" not in err and "secret detail" not in err and "ValueError" in err
    assert out == ""


def test_debug_env_prints_traceback_to_stderr(capsys, monkeypatch):
    monkeypatch.setenv("SABER11_DEBUG", "1")
    def boom(cfg):
        raise ValueError("secret detail")
    assert main(["run"], run_fn=boom) == 2
    out, err = capsys.readouterr()
    assert "Traceback" in err and out == ""


def test_stage_logs_go_to_stderr_and_stdout_has_only_the_pdf(capsys):
    import logging

    def fake_run(cfg):
        logging.getLogger("saber11.pipeline").info('{"stage": "ingest"}')
        return SimpleNamespace(pdf=Path("out/x.pdf"))
    assert main(["run"], run_fn=fake_run) == 0
    out, err = capsys.readouterr()
    assert out.strip() == "out/x.pdf" and '"stage": "ingest"' in err


def test_help_exits_zero(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--help"])
    assert exc.value.code == 0

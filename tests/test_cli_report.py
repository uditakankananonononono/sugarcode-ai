"""CLI report subcommands (drop 62)."""
import json

from sugarcode.cli import main

FAKE = {"gene": "RB1", "notation": "c.2490-28T>G", "verdict": "strong loss",
        "delta": -0.7937}


def _patch_assessment(monkeypatch):
    monkeypatch.setattr("sugarcode.cli.live_splice_assessment",
                        lambda gene, notation, offline=False, transcript=None: FAKE)


def test_cli_report_splice_html_stdout(monkeypatch, capsys):
    _patch_assessment(monkeypatch)
    assert main(["report", "splice", "RB1", "c.2490-28T>G"]) == 0
    out = capsys.readouterr().out
    assert out.startswith("<!DOCTYPE html>") and "RB1" in out


def test_cli_report_splice_md_to_file(monkeypatch, capsys, tmp_path):
    _patch_assessment(monkeypatch)
    f = tmp_path / "rep.md"
    assert main(["report", "splice", "RB1", "c.2490-28T>G",
                 "--format", "md", "--out", str(f)]) == 0
    assert f.read_text().startswith("# Splice assessment: RB1")
    assert "wrote" in capsys.readouterr().out


def test_cli_report_splice_json_bundle(monkeypatch, capsys):
    _patch_assessment(monkeypatch)
    assert main(["report", "splice", "RB1", "c.2490-28T>G",
                 "--format", "json"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert set(out["files"]) == {"report.html", "report.md"}
    assert all(len(v["sha256"]) == 64 for v in out["files"].values())
    assert out["metadata"]["disclaimer"]


def test_cli_report_notebook_writes_valid_ipynb(capsys, tmp_path):
    f = tmp_path / "nb.ipynb"
    assert main(["report", "notebook", "RB1", "c.2490-28T>G",
                 "--out", str(f)]) == 0
    nb = json.loads(f.read_text())
    assert nb["nbformat"] == 4 and "valid=True" in capsys.readouterr().out


def test_cli_report_validate_notebook(capsys, tmp_path):
    f = tmp_path / "nb.ipynb"
    assert main(["report", "notebook", "RB1", "c.2490-28T>G",
                 "--out", str(f)]) == 0
    capsys.readouterr()
    assert main(["report", "validate-notebook", str(f)]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["valid"] and out["problems"] == []


def test_cli_modules_now_89(capsys):
    assert main(["modules"]) == 0
    assert capsys.readouterr().out.startswith("89 modules")

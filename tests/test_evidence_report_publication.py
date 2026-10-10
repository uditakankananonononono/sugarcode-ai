"""PREP-NORUN: authored script publication canaries, not executed by builder."""
import importlib.util
from pathlib import Path
import subprocess
import sys

import pytest


@pytest.fixture
def script():
    path = Path(__file__).resolve().parents[1] / "scripts/evidence_report.py"
    spec = importlib.util.spec_from_file_location("evidence_report_proposal", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


HEADLINES = (
    "fixtures: 3  unique pathogenic: 20  unique benign: 4\n"
    "canonical U2 (GT/GC donor, AG acceptor): 10/10 called loss\n"
    "canonical AT-AC (U12 matrices, drop 27): 2/2 called loss\n"
    "benign specificity: 3/4\n"
)


def old_report(tmp_path):
    destination = tmp_path / "docs/EVIDENCE.md"
    destination.parent.mkdir()
    destination.write_bytes(b"original report\r\n\x00untouched")
    return destination, destination.read_bytes()


@pytest.mark.parametrize("output,returncode", [
    ("", 1), (HEADLINES, 1), ("fixtures: 3  unique pathogenic: 20  unique benign: 4\n", 0),
    (HEADLINES + "benign specificity: 3/4\n", 0),
    (HEADLINES.replace("3/4", "garbage"), 0),
    (HEADLINES.replace("3/4", "5/4"), 0),
    (HEADLINES.replace("unique benign: 4", "unique benign: -4"), 0),
])
def test_failed_partial_malformed_child_preserves_old_bytes(script, tmp_path, monkeypatch, output, returncode):
    destination, before = old_report(tmp_path)
    monkeypatch.setattr(script.subprocess, "run", lambda *a, **k:
                        subprocess.CompletedProcess(a[0], returncode, output, "failure"))
    with pytest.raises(script.EvidenceReportFailure, match="pooled"):
        script.main(tmp_path)
    assert destination.read_bytes() == before
    assert sorted(p.name for p in destination.parent.iterdir()) == ["EVIDENCE.md"]


def test_child_launch_failure_preserves_old_bytes(script, tmp_path, monkeypatch):
    destination, before = old_report(tmp_path)
    def fail(*args, **kwargs):
        raise OSError("launch failed")
    monkeypatch.setattr(script.subprocess, "run", fail)
    with pytest.raises(script.EvidenceReportFailure, match="launch"):
        script.main(tmp_path)
    assert destination.read_bytes() == before


def test_current_interpreter_repo_root_and_original_headline_order(script, tmp_path, monkeypatch):
    def child(command, **kwargs):
        assert command == [sys.executable, str(tmp_path / "scripts/pooled_splice_stats.py")]
        assert kwargs == {"cwd": tmp_path, "capture_output": True, "text": True}
        return subprocess.CompletedProcess(command, 0, HEADLINES + "ignored detail\n", "")
    monkeypatch.setattr(script.subprocess, "run", child)
    assert script.pooled_headlines(tmp_path) == HEADLINES.splitlines()


@pytest.mark.parametrize("stage", ["fixture", "section"])
def test_later_render_failure_preserves_old_bytes(script, tmp_path, monkeypatch, stage):
    destination, before = old_report(tmp_path)
    monkeypatch.setattr(script, "pooled_headlines", lambda root: HEADLINES.splitlines())
    if stage == "section":
        monkeypatch.setattr(script, "load", lambda root, name: {})
    with pytest.raises(script.EvidenceReportFailure, match="fixture"):
        script.main(tmp_path)
    assert destination.read_bytes() == before


@pytest.mark.parametrize("stage", ["fsync", "replace", "write"])
def test_atomic_publication_failure_preserves_old_bytes(script, tmp_path, monkeypatch, stage):
    destination, before = old_report(tmp_path)
    def fail(*args, **kwargs):
        raise OSError("simulated publication failure")
    if stage in ("fsync", "replace"):
        monkeypatch.setattr(script.os, stage, fail)
    else:
        original = script.tempfile.NamedTemporaryFile
        class BadWrite:
            def __init__(self):
                self.file = original(mode="w", encoding="utf-8", dir=destination.parent, delete=False)
                self.name = self.file.name
            def __enter__(self):
                return self
            def write(self, content):
                self.file.write("partial")
                raise OSError("partial write")
            def __exit__(self, *args):
                self.file.close()
        monkeypatch.setattr(script.tempfile, "NamedTemporaryFile", lambda **kwargs: BadWrite())
    with pytest.raises(script.EvidenceReportFailure, match="publication"):
        script.publish_report("new complete report\n", destination)
    assert destination.read_bytes() == before
    assert sorted(p.name for p in destination.parent.iterdir()) == ["EVIDENCE.md"]


def test_success_publishes_exact_content_and_only_then_prints(script, tmp_path, monkeypatch, capsys):
    destination, _ = old_report(tmp_path)
    report = "all existing sections\n"
    monkeypatch.setattr(script, "render_report", lambda root: report)
    script.main(tmp_path)
    assert destination.read_bytes() == report.encode("utf-8")
    assert capsys.readouterr().out == report + "\n"
    assert sorted(p.name for p in destination.parent.iterdir()) == ["EVIDENCE.md"]


def test_existing_real_fixtures_render_same_report_as_published_base(script, monkeypatch):
    # No child executed in this case. Locks complete rendering against base doc.
    root = Path(__file__).resolve().parents[1]
    expected = (root / "docs/EVIDENCE.md").read_text()
    pooled = [line[2:] for line in expected.splitlines()
              if line.startswith(("- fixtures:", "- canonical", "- benign specificity:"))]
    assert len(pooled) == 4
    monkeypatch.setattr(script, "pooled_headlines", lambda root: pooled)
    assert script.render_report(root) == expected

"""H25 characterization of the `sugarcode shared dataset` ValueError boundary.

AUTHORED BY READING ONLY, NOT RUN. Source read at 9a6b9380 (cli.py 281-304,
llm/shared.py 155-156, llm/dataset.py, instinct_models/training/dataset.py).
No product change. Excluded: interpreter version texts, the success dataset.
"""
import json

import pytest

from instinct_models.training.dataset import ExampleRow, build_needle_jsonl
from sugarcode.cli import main


def _run(capsys, argv):
    rc = main(argv)
    return rc, capsys.readouterr().out


def test_cli_maps_valueerror_to_error_json_exit_1(monkeypatch, tmp_path, capsys):
    def boom(*a, **k):
        raise ValueError("x")
    monkeypatch.setattr("sugarcode.llm.shared.build_shared_needle_dataset", boom)
    rc, out = _run(capsys, ["shared", "dataset", str(tmp_path / "n.jsonl")])
    assert rc == 1
    assert json.loads(out) == {"error": "x"}


def test_cli_success_passes_manifest_through_rc0(monkeypatch, tmp_path, capsys):
    manifest = {"product": "sugarcode", "rows": 3, "sentinel": "h25"}
    monkeypatch.setattr("sugarcode.llm.shared.build_shared_needle_dataset", lambda *a, **k: manifest)
    rc, out = _run(capsys, ["shared", "dataset", str(tmp_path / "n.jsonl")])
    assert rc == 0
    assert json.loads(out) == manifest


@pytest.mark.parametrize("exc", [OSError("disk"), RuntimeError("rt")])
def test_cli_only_catches_valueerror(monkeypatch, tmp_path, capsys, exc):
    def boom(*a, **k):
        raise exc
    monkeypatch.setattr("sugarcode.llm.shared.build_shared_needle_dataset", boom)
    with pytest.raises(type(exc)):
        main(["shared", "dataset", str(tmp_path / "n.jsonl")])


class _Stub:
    product = "sugarcode"

    def __init__(self, rows):
        self._rows = rows

    def rows(self):
        return self._rows


@pytest.mark.parametrize("rows", [
    [],
    [ExampleRow(query="q", tools=[], answers=[], confirmed=False, source_ref="r1")],
])
def test_build_needle_jsonl_no_usable_rows_raises_and_writes_nothing(tmp_path, rows):
    out = tmp_path / "n.jsonl"
    with pytest.raises(ValueError) as ei:
        build_needle_jsonl(_Stub(rows), out)
    assert str(ei.value) == "no usable rows after filtering"
    assert not out.exists()
    assert not (tmp_path / "n.jsonl.manifest.json").exists()


def test_real_cli_max_tools_zero_reports_no_usable_rows(tmp_path, capsys):
    # Runs the REAL catalog and shared dataset (authored only; the peer's audit runs it).
    out = tmp_path / "n.jsonl"
    rc, text = _run(capsys, ["shared", "dataset", str(out), "--max-tools", "0"])
    assert rc == 1
    assert json.loads(text) == {"error": "no usable rows after filtering"}
    assert not out.exists()
    assert not (tmp_path / "n.jsonl.manifest.json").exists()

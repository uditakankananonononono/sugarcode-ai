"""CSV/TSV exporters and evidence bundles."""
import hashlib
import json

import pytest

from sugarcode.report import to_csv, to_tsv, make_bundle, write_bundle


def test_csv_quoting_and_none():
    rows = [{"a": 'x,"y"', "b": None}, {"a": "line\nbreak", "b": 2}]
    out = to_csv(rows, ["a", "b"])
    lines = out.splitlines()
    assert lines[0] == "a,b"
    assert '"x,""y""",' in lines[1] and lines[1].endswith(",")
    assert '"line' in lines[2]


def test_csv_default_columns_sorted_union():
    out = to_csv([{"b": 1}, {"a": 2}])
    assert out.splitlines()[0] == "a,b"


def test_csv_unknown_column_raises():
    with pytest.raises(ValueError):
        to_csv([{"a": 1, "extra": 2}], ["a"])


def test_tsv_uses_tabs():
    out = to_tsv([{"a": 1, "b": 2}])
    assert out.splitlines()[0] == "a\tb"


def test_bundle_checksums_real():
    b = make_bundle("n", {"a.txt": "hello"}, created_utc="2026-09-24T00:00:00+00:00")
    a = b["artifacts"]["a.txt"]
    assert a["sha256"] == hashlib.sha256(b"hello").hexdigest()
    assert a["bytes"] == 5
    assert b["created_utc"] == "2026-09-24T00:00:00+00:00"


def test_bundle_rejects_unsafe_names():
    with pytest.raises(ValueError):
        make_bundle("n", {"../evil": "x"})
    with pytest.raises(ValueError):
        make_bundle("n", {})
    with pytest.raises(TypeError):
        make_bundle("n", {"a.txt": b"bytes"})


def test_write_bundle_roundtrip(tmp_path):
    b = make_bundle("n", {"a.txt": "hello"}, metadata={"k": 1},
                    created_utc="2026-09-24T00:00:00+00:00")
    r = write_bundle(b, tmp_path)
    assert (tmp_path / "a.txt").read_text() == "hello"
    man = json.loads((tmp_path / "MANIFEST.json").read_text())
    assert man["files"]["a.txt"]["sha256"] == hashlib.sha256(b"hello").hexdigest()
    assert man["metadata"]["k"] == 1 and len(r["files"]) == 2

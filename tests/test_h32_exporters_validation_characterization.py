"""H32 characterization of report/exporters.py validation and edge rendering (current behavior).

AUTHORED BY READING ONLY, NOT RUN. Source read at fb9e276a: exporters.py 1-104 in full.
Findings only. The renderings in test 4 (False as text, empty field) and test 5 (missing key as an
empty field) are predictions about the stdlib csv module, NOT verified; the peer's run decides, and a
different actual would be pinned by an explicit later correction.
"""
import hashlib

import pytest

from sugarcode.report import make_bundle, to_csv


@pytest.mark.parametrize("rows", ["x", [1]])
def test_to_csv_rejects_non_list_or_non_dict_members(rows):
    with pytest.raises(TypeError):
        to_csv(rows)


@pytest.mark.parametrize("columns", [[], ["a", ""], ["a", 1]])
def test_to_csv_rejects_bad_explicit_columns(columns):
    with pytest.raises(ValueError, match="non-empty list of names"):
        to_csv([{"a": 1}], columns)


def test_to_csv_explicit_column_order_is_kept():
    assert to_csv([{"b": 1, "a": 2}], ["b", "a"]) == "b,a\n1,2\n"


def test_to_csv_zero_false_and_empty_string_literal_rendering():
    assert to_csv([{"a": 0, "b": False, "c": ""}], ["a", "b", "c"]) == "a,b,c\n0,False,\n"


def test_to_csv_missing_key_renders_as_empty_field():
    assert to_csv([{"a": 1}], ["a", "b"]) == "a,b\n1,\n"


@pytest.mark.parametrize("name", ["", "  ", 5])
def test_make_bundle_rejects_blank_or_non_str_name(name):
    with pytest.raises(ValueError):
        make_bundle(name, {"a.txt": "x"})


@pytest.mark.parametrize("filename", ["a\\b", "dir/x", "", ".", "..", 5])
def test_make_bundle_rejects_unsafe_or_non_str_filenames(filename):
    with pytest.raises(ValueError):
        make_bundle("n", {filename: "x"})


def test_make_bundle_non_ascii_bytes_sha_default_metadata_and_generator():
    b = make_bundle("n", {"a.txt": "\u00e9"}, created_utc="t")
    a = b["artifacts"]["a.txt"]
    assert a["bytes"] == 2
    assert a["sha256"] == hashlib.sha256("\u00e9".encode()).hexdigest()
    assert b["metadata"] == {}
    assert b["generator"] == "sugarcode-ai report engine"

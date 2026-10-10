"""AUTHORED, NOT RUN. Tests for self_improve.header_text (G01 prep).
Import path unverified against the pyproject layout."""
import ast
import json

import pytest

from sugarcode.self_improve.header_text import encode_header_text, render_header_fields

HOSTILE = [
    '"""', 'a"""b', '"', "\\", "\\\"\"\"", "a\nb", "a\r\nb", "a\rb", "a\u2028b", "a\u2029b",
    "\x00\x01\x1f", "\x7f", "'''", "{x}", "{0}", "%s", "# c", '""" ; import os ; """',
    "\ud800", "\U0001f642", "../escape", " ", "\t",
]
UNICODE_OK = ["módulo", "中文", "Démo_1"]


def _doc(enc_slug, enc_sig):
    return '"""Auto-generated.\n\nModule: %s\nGap: %s\nDo not hand-edit.\n"""\n' % (enc_slug, enc_sig)


@pytest.mark.parametrize("v", HOSTILE + UNICODE_OK + [""])
def test_round_trips_exactly(v):
    assert json.loads(encode_header_text(v)) == v


@pytest.mark.parametrize("v", HOSTILE + UNICODE_OK + [""])
def test_single_line_ascii_only(v):
    enc = encode_header_text(v)
    assert enc.isascii()
    assert "\n" not in enc and "\r" not in enc and "\u2028" not in enc and "\u2029" not in enc
    assert enc.startswith('"') and enc.endswith('"')


def test_unicode_preserved_not_refused():
    for v in UNICODE_OK:
        assert json.loads(encode_header_text(v)) == v


def test_empty_signature_accepted():
    assert encode_header_text("") == '""'
    assert render_header_fields("m", "") == ('"m"', '""')


def test_no_unescaped_triple_quote():
    for v in HOSTILE:
        assert '"""' not in encode_header_text(v).replace('\\"', "")


def test_matches_json_dumps_ensure_ascii():
    for v in HOSTILE + UNICODE_OK:
        assert encode_header_text(v) == json.dumps(v, ensure_ascii=True)


@pytest.mark.parametrize("sig", HOSTILE + UNICODE_OK + [""])
@pytest.mark.parametrize("slug", HOSTILE[:8] + UNICODE_OK)
def test_docstring_stays_one_statement_with_both_fields_on_own_lines(slug, sig):
    es, eg = render_header_fields(slug, sig)
    src = _doc(es, eg)
    tree = ast.parse(src)
    assert len(tree.body) == 1 and isinstance(tree.body[0], ast.Expr)
    lines = src.split("\n")
    assert sum(1 for x in lines if x.startswith("Module: ")) == 1
    assert sum(1 for x in lines if x.startswith("Gap: ")) == 1
    assert len(lines) == 7  # opening, blank, Module, Gap, note, closing, trailing ""


def test_no_slug_validation_here():
    for v in ["../escape", "---", "__", "a b", "-", ""]:
        encode_header_text(v)  # must not raise


@pytest.mark.parametrize("v", [None, 7, 1.5, True, b"x", ["a"], {"a": 1}])
def test_non_str_is_coerced_with_str_like_format_did(v):
    assert encode_header_text(v) == json.dumps(str(v), ensure_ascii=True)
    assert json.loads(encode_header_text(v)) == "{}".format(v)


def test_none_and_int_examples():
    assert encode_header_text(None) == '"None"'
    assert encode_header_text(7) == '"7"'
    assert render_header_fields(None, 7) == ('"None"', '"7"')


def test_str_subclass_encodes_as_its_text():
    class S(str):
        pass
    assert encode_header_text(S("ab")) == '"ab"'

"""AUTHORED, NOT RUN. Tests for sugarcode.tools.splice_vus_input (prep)."""
from __future__ import annotations

import math

import pytest

from sugarcode.tools import splice_vus_input as si

R = "A" * 40 + "C" + "G" * 40
A = "A" * 40 + "T" + "G" * 40


def _code(exc_info):
    return exc_info.value.code


def test_error_is_valueerror_with_field_and_code():
    with pytest.raises(ValueError) as ei:
        si.validate_base("N", "ref")
    assert isinstance(ei.value, si.SpliceInputError)
    assert ei.value.field == "ref" and ei.value.code == "alphabet"


def test_constants_match_triage_module_source_text():
    import pathlib, re
    src = (pathlib.Path(si.__file__).with_name("splice_vus_triage.py")).read_text(encoding="utf-8")
    assert re.search(r"^F = 40$", src, re.M)
    assert si.F == 40 and si.CTX_LEN == 81


@pytest.mark.parametrize("v,exp", [("A", "A"), ("c", "C"), ("G", "G"), ("t", "T")])
def test_base_accepts_acgt_and_normalizes(v, exp):
    assert si.validate_base(v, "ref") == exp


@pytest.mark.parametrize("v,code", [
    ("N", "alphabet"), ("R", "alphabet"), ("-", "alphabet"), (" ", "alphabet"), ("U", "alphabet"),
    ("", "length"), ("AT", "length"), ("AA", "length"),
    (None, "type"), (65, "type"), (b"A", "type"),
])
def test_base_rejections(v, code):
    with pytest.raises(si.SpliceInputError) as ei:
        si.validate_base(v, "alt")
    assert _code(ei) == code


def test_ref_alt_identical_rejected_even_across_case():
    with pytest.raises(si.SpliceInputError) as ei:
        si.validate_ref_alt("a", "A")
    assert _code(ei) == "identical"


def test_ref_alt_ok():
    assert si.validate_ref_alt("g", "a") == ("G", "A")


@pytest.mark.parametrize("v,exp", [(41, 41), ("41", 41), ("1000000", 1000000), (10**12, 10**12)])
def test_pos_accepts(v, exp):
    assert si.validate_pos(v) == exp


@pytest.mark.parametrize("v,code", [
    (40, "range"), (0, "range"), (-5, "range"), ("40", "range"), ("0", "range"),
    ("41.0", "type"), ("+41", "type"), ("-41", "type"), (" 41", "type"), ("41 ", "type"),
    ("4e1", "type"), ("", "type"), ("\u0664\u0661", "type"),
    (41.0, "type"), (True, "type"), (None, "type"),
])
def test_pos_rejections(v, code):
    with pytest.raises(si.SpliceInputError) as ei:
        si.validate_pos(v)
    assert _code(ei) == code


@pytest.mark.parametrize("v", ["chr1", "1", "chrM", "MT", "HLA-A*01"])
def test_chrom_accepts(v):
    assert si.validate_chrom(v) == v


@pytest.mark.parametrize("v", ["", " ", "chr 1", "chr1\t", "chr1\n", None, 1])
def test_chrom_rejections(v):
    with pytest.raises(si.SpliceInputError) as ei:
        si.validate_chrom(v)
    assert _code(ei) == "format"


def test_genome_row_ok_and_normalized():
    assert si.validate_genome_row("chr7", "117559590", "c", "t") == {
        "chrom": "chr7", "pos": 117559590, "ref": "C", "alt": "T"}


@pytest.mark.parametrize("kwargs,field", [
    (dict(chrom="", pos=100, ref="A", alt="C"), "chrom"),
    (dict(chrom="1", pos=10, ref="A", alt="C"), "pos"),
    (dict(chrom="1", pos=100, ref="AC", alt="C"), "ref"),
    (dict(chrom="1", pos=100, ref="A", alt="AT"), "alt"),
    (dict(chrom="1", pos=100, ref="A", alt="N"), "alt"),
])
def test_genome_row_rejections_name_the_field(kwargs, field):
    with pytest.raises(si.SpliceInputError) as ei:
        si.validate_genome_row(**kwargs)
    assert ei.value.field == field


def test_contexts_ok_and_normalized():
    r, a = si.validate_contexts(R.lower(), A.lower())
    assert (r, a) == (R, A) and len(r) == 81


def test_contexts_flank_n_tolerated_when_identical():
    r = "N" + R[1:40] + "C" + R[41:80] + "N"
    a = "N" + A[1:40] + "T" + A[41:80] + "N"
    assert si.validate_contexts(r, a) == (r, a)


def test_contexts_flank_n_in_only_one_rejected_as_flank_mismatch():
    r = "N" + R[1:]
    with pytest.raises(si.SpliceInputError) as ei:
        si.validate_contexts(r, A)
    assert _code(ei) == "flanks"


@pytest.mark.parametrize("n", [0, 1, 80, 82, 100])
def test_contexts_length_rejected(n):
    bad = "A" * n
    with pytest.raises(si.SpliceInputError) as ei:
        si.validate_contexts(bad, A)
    assert (ei.value.field, ei.value.code) == ("ref_ctx", "length")
    with pytest.raises(si.SpliceInputError) as ei:
        si.validate_contexts(R, bad)
    assert (ei.value.field, ei.value.code) == ("alt_ctx", "length")


@pytest.mark.parametrize("ch", ["R", "-", " ", "U", "Y"])
@pytest.mark.parametrize("idx", [0, 20, 39, 41, 80])
def test_contexts_bad_alphabet_in_flank_rejected(ch, idx):
    r = R[:idx] + ch + R[idx + 1:]
    with pytest.raises(si.SpliceInputError) as ei:
        si.validate_contexts(r, A)
    assert (ei.value.field, ei.value.code) == ("ref_ctx", "alphabet")


def test_contexts_center_n_rejected_each_side():
    with pytest.raises(si.SpliceInputError) as ei:
        si.validate_contexts(R[:40] + "N" + R[41:], A)
    assert (ei.value.field, ei.value.code) == ("ref_ctx", "center")
    with pytest.raises(si.SpliceInputError) as ei:
        si.validate_contexts(R, A[:40] + "N" + A[41:])
    assert (ei.value.field, ei.value.code) == ("alt_ctx", "center")


def test_contexts_center_must_differ():
    with pytest.raises(si.SpliceInputError) as ei:
        si.validate_contexts(R, R)
    assert _code(ei) == "identical"


@pytest.mark.parametrize("idx", [0, 39, 41, 80])
def test_contexts_flank_difference_rejected(idx):
    a = A[:idx] + ("T" if A[idx] != "T" else "A") + A[idx + 1:]
    with pytest.raises(si.SpliceInputError) as ei:
        si.validate_contexts(R, a)
    assert _code(ei) == "flanks"


@pytest.mark.parametrize("bad", [None, 5, b"A" * 81, ["A"] * 81])
def test_contexts_type_rejected(bad):
    with pytest.raises(si.SpliceInputError) as ei:
        si.validate_contexts(bad, A)
    assert _code(ei) == "type"
    with pytest.raises(si.SpliceInputError) as ei:
        si.validate_contexts(R, bad)
    assert _code(ei) == "type"


@pytest.mark.parametrize("v,exp", [(0.03, 0.03), (0.5, 0.5), (1e-9, 1e-9), (0.999999, 0.999999)])
def test_prior_accepts(v, exp):
    assert si.validate_prior(v) == exp


@pytest.mark.parametrize("v,code", [
    (0, "range"), (0.0, "range"), (1, "range"), (1.0, "range"), (-0.1, "range"), (1.5, "range"),
    (math.nan, "range"), (math.inf, "range"), (-math.inf, "range"),
    ("0.03", "type"), (None, "type"), (True, "type"),
])
def test_prior_rejections(v, code):
    with pytest.raises(si.SpliceInputError) as ei:
        si.validate_prior(v)
    assert _code(ei) == code


def test_module_has_no_heavy_imports():
    import pathlib
    src = pathlib.Path(si.__file__).read_text(encoding="utf-8")
    for name in ("torch", "numpy", "maxentpy", "spliceai", "twobitreader"):
        assert f"import {name}" not in src and f"from {name}" not in src


def test_prior_huge_int_is_typed_not_overflowerror():
    with pytest.raises(si.SpliceInputError) as ei:
        si.validate_prior(10**1000)
    assert (ei.value.field, ei.value.code) == ("prior", "range")
    assert isinstance(ei.value.__cause__, OverflowError)
    with pytest.raises(si.SpliceInputError):
        si.validate_prior(-(10**1000))


@pytest.mark.parametrize("n", [5000, 100000])
def test_pos_very_long_digit_string_is_typed(n):
    with pytest.raises(si.SpliceInputError) as ei:
        si.validate_pos("9" * n)
    assert (ei.value.field, ei.value.code) == ("pos", "range")


def test_pos_huge_exact_int_is_accepted_unchanged():
    assert si.validate_pos(10**30) == 10**30

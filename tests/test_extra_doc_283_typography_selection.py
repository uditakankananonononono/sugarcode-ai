import itertools
from fractions import Fraction
import pytest
from sugarcode.extra_doc import typography_selection as t

A = t.analyze_typography


def F(n, cat, xh):
    return {"name": n, "category": cat, "x_height": xh}


FONTS = [F("Alpha", "serif", 0.5), F("Beta", "sans", 0.52)]


def test_constants():
    assert t.CATEGORIES == ("serif", "sans", "mono", "display", "script")
    assert (t.MAX_FONTS, t.MAX_HEADINGS, t.MAX_NAME, t.MIN_BODY_PX, t.MAX_PX) == (30, 10, 40, 16, 1000)
    assert t.LINE_HEIGHT_RANGE == (Fraction(13, 10), Fraction(17, 10)) and t.MEASURE_RANGE == (45, 75)
    assert t.MIN_SCALE_STEP == Fraction(6, 5) and t.XHEIGHT_GAP == Fraction(1, 20)
    assert t.STATUS_NOTE.startswith("PARTIAL")


def test_hand_literal():
    r = A(16, 24, 60, [20, 25, 30, 60], FONTS)
    assert r["line_height_ratio"] == 1.5 and r["line_height_ok"] and r["measure_ok"] and r["body_size_ok"]
    assert [(s["from"], s["ratio"], s["ok"]) for s in r["heading_steps"]] == [(20.0, 1.25, True), (25.0, 1.2, True), (30.0, 2.0, True)]
    assert r["headings_above_body"] is True and r["headings_descending_or_flat"] is False
    assert r["font_pairs"] == [{"a": "Alpha", "b": "Beta", "xheight_gap": pytest.approx(0.02), "verdict": "contrast"}]


def test_boundaries_inclusive():
    def lh(px, body=10):
        return A(body, px, 60, [], FONTS)["line_height_ok"]
    assert (lh(13), lh(12.9), lh(17), lh(17.1)) == (True, False, True, False)
    def ms(n):
        return A(16, 24, n, [], FONTS)["measure_ok"]
    assert (ms(45), ms(44), ms(75), ms(76)) == (True, False, True, False)
    assert (A(16, 24, 60, [], FONTS)["body_size_ok"], A(15.9, 24, 60, [], FONTS)["body_size_ok"]) == (True, False)
    assert A(10, 15, 60, [10, 12], FONTS)["heading_steps"][0]["ok"] is True       # exactly 1.2
    assert A(10, 15, 60, [10, 11.9], FONTS)["heading_steps"][0]["ok"] is False
    assert A(10, 15, 60, [11, 12], FONTS)["headings_above_body"] is True
    assert A(10, 15, 60, [10, 12], FONTS)["headings_above_body"] is False
    assert A(10, 15, 60, [30, 20], FONTS)["headings_descending_or_flat"] is True
    assert A(10, 15, 60, [20, 20], FONTS)["headings_descending_or_flat"] is False
    assert A(10, 15, 60, [], FONTS)["headings_above_body"] is True and A(10, 15, 60, [], FONTS)["heading_steps"] == []


def test_pair_verdicts_hand_literals():
    fonts = [F("a", "serif", 0.5), F("b", "serif", 0.52), F("c", "serif", 0.56), F("d", "sans", 0.5), F("e", "sans", 0.56),
             F("f", "mono", 0.45)]
    v = {(p["a"], p["b"]): p["verdict"] for p in A(16, 24, 60, [], fonts)["font_pairs"]}
    assert v[("a", "b")] == "too_similar"                       # gap 0.02
    assert v[("a", "c")] == "same_category_distinct_xheight"    # gap 0.06
    assert v[("a", "d")] == "contrast"                          # gap 0
    assert v[("a", "e")] == "contrast_xheight_mismatch"         # gap 0.06
    assert len(v) == 15
    # gap exactly 0.05 counts as distinct / mismatch (not below the 0.05 limit); Fractions keep it exact
    ex = [F("p", "serif", Fraction(1, 2)), F("q", "serif", Fraction(11, 20)), F("r", "sans", Fraction(11, 20))]
    vv = {(p["a"], p["b"]): p["verdict"] for p in A(16, 24, 60, [], ex)["font_pairs"]}
    assert vv[("p", "q")] == "same_category_distinct_xheight" and vv[("p", "r")] == "contrast_xheight_mismatch"
    assert vv[("q", "r")] == "contrast"


def test_pairs_enumerated_like_itertools():
    names = [F(f"f{i}", "sans", 0.4 + i * 0.01) for i in range(6)]
    got = [(p["a"], p["b"]) for p in A(16, 24, 60, [], names)["font_pairs"]]
    assert got == list(itertools.combinations([f"f{i}" for i in range(6)], 2))


def test_validation():
    ok = (16, 24, 60, [20], FONTS)
    for pos, bad, m in [(0, True, "body_px"), (0, 0, r"body_px: must be within \[1, 1000\]"), (0, 1001, "body_px: must be within"),
                        (0, "16", "number required"), (0, float("nan"), "finite"), (0, 1e10, "magnitude above 1e9"),
                        (1, 0, "line_height_px"), (2, 0, "measure_chars"), (2, 1001, "measure_chars: must be within")]:
        a = list(ok); a[pos] = bad
        with pytest.raises(ValueError, match=m):
            A(*a)
    for hp, m in [("x", "heading_px: list"), ([0], r"heading_px\[0\]"), ([20] * 11, "at most 10"), ([True], "number required")]:
        with pytest.raises(ValueError, match=m):
            A(16, 24, 60, hp, FONTS)
    assert len(A(16, 24, 60, [20] * 10, FONTS)["heading_steps"]) == 9
    for fs, m in [([], "1..30"), ("x", "1..30"), ([5], r"fonts\[0\]: dict"), ([F("", "sans", .5)], "name must"),
                  ([F("x" * 41, "sans", .5)], "name must"), ([F("a", "slab", .5)], "category must be one of"),
                  ([F("a", "sans", .19)], r"x_height: must be within"), ([F("a", "sans", .81)], r"x_height: must be within"),
                  ([F("a", "sans", None)], "number required"), ([F("a", "sans", .5), F("a", "serif", .5)], "duplicate name")]:
        with pytest.raises(ValueError, match=m):
            A(16, 24, 60, [], fs)
    assert A(16, 24, 60, [], [F("x" * 40, "script", 0.2)])["font_pairs"] == []
    assert A(16, 24, 60, [], [F("x", "display", Fraction(4, 5))])["font_pairs"] == []
    many = [F(f"f{i}", "sans", .5) for i in range(31)]
    with pytest.raises(ValueError, match="1..30"):
        A(16, 24, 60, [], many)
    assert len(A(16, 24, 60, [], many[:30])["font_pairs"]) == 435
    assert A(1, 1, 1, [], FONTS)["line_height_ratio"] == 1.0 and A(1000, 1000, 1000, [], FONTS)["body_size_ok"] is True


def test_heading_and_cap_edges():
    assert A(16, 24, 60, [1], FONTS)["headings_above_body"] is False
    assert A(1, 2, 60, [1, 1000], FONTS)["heading_steps"][0]["ratio"] == 1000.0
    with pytest.raises(ValueError, match=r"heading_px\[0\]: must be within"):
        A(16, 24, 60, [1001], FONTS)
    with pytest.raises(ValueError, match=r"heading_px\[0\]: must be within"):
        A(16, 24, 60, [0.5], FONTS)
    with pytest.raises(ValueError, match="magnitude above 1e9"):
        A(10 ** 9 + 1, 24, 60, [], FONTS)
    with pytest.raises(ValueError, match=r"body_px: must be within"):
        A(10 ** 9, 24, 60, [], FONTS)
    with pytest.raises(ValueError, match="magnitude above 1e9"):
        A(16, -(10 ** 9) - 1, 60, [], FONTS)

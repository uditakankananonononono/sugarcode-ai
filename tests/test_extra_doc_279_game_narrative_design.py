import math
import random
from fractions import Fraction
import pytest
from sugarcode.extra_doc import game_narrative_design as g

A = g.analyze_alignment


def beats(*t):
    return [{"id": f"b{i}", "tension": x} for i, x in enumerate(t)]


def mechs(*t):
    return [{"id": f"m{i}", "intensity": x} for i, x in enumerate(t)]


def L(*pairs):
    return [{"beat": f"b{a}", "mechanic": f"m{c}"} for a, c in pairs]


def test_constants():
    assert (g.MAX_BEATS, g.MAX_MECHANICS, g.MAX_LINKS, g.MAX_ID, g.SCALE_MAX, g.DEFAULT_THRESHOLD) == (200, 200, 1000, 40, 10, 3)
    assert g.STATUS_NOTE.startswith("PARTIAL")


def test_hand_literal_example():
    # tensions 2,5,8,9 ; intensities by link: b0->m0(2), b1->m1(4), b2->m0 and m2 (2,6 mean 4), b3 unlinked; m3 unused
    r = A(beats(2, 5, 8, 9), mechs(2, 4, 6, 9), L((0, 0), (1, 1), (2, 0), (2, 2)))
    assert [x["intensity"] for x in r["beats"]] == [2.0, 4.0, 4.0, None]
    assert [x["gap"] for x in r["beats"]] == [0.0, 1.0, 4.0, None]
    assert [x["dissonant"] for x in r["beats"]] == [False, False, True, None]
    assert r["coverage"] == 0.75
    assert r["mean_abs_gap"] == pytest.approx(5 / 3)
    assert r["unlinked_beats"] == ["b3"] and r["unused_mechanics"] == ["m3"]
    # x = 2,5,8 ; y = 2,4,4 -> means 5, 10/3 ; sxx=18 ; syy=8/3 ; sxy=(-3)(-4/3)+0+(3)(2/3)=6
    assert r["correlation"] == pytest.approx(6 / math.sqrt(18 * 8 / 3))
    assert r["correlation"] == pytest.approx(0.8660254037844387)
    assert r["threshold"] == 3.0


def test_threshold_boundary_is_inclusive():
    r = A(beats(7), mechs(4), L((0, 0)))
    assert r["beats"][0]["dissonant"] is True
    assert A(beats(7), mechs(4), L((0, 0)), 3.5)["beats"][0]["dissonant"] is False
    assert A(beats(7), mechs(4), L((0, 0)), 3)["beats"][0]["gap"] == 3.0


def test_correlation_edges():
    assert A(beats(1, 2), mechs(5), L((0, 0)))["correlation"] is None            # constant intensity
    assert A(beats(1), mechs(5), L((0, 0)))["correlation"] is None               # one point
    assert A(beats(1, 2, 3), mechs(9, 8, 7), L((0, 0), (1, 1), (2, 2)))["correlation"] == pytest.approx(-1.0)
    assert A(beats(1, 2, 3), mechs(2, 4, 6), L((0, 0), (1, 1), (2, 2)))["correlation"] == pytest.approx(1.0)
    r = A(beats(1, 2), mechs(5), [])
    assert r["coverage"] == 0.0 and r["mean_abs_gap"] is None and r["correlation"] is None


def test_random_matches_brute_force_pearson():
    rng = random.Random(279)
    for _ in range(40):
        n = rng.randint(2, 6)
        t = [rng.randint(0, 10) for _ in range(n)]
        iv = [rng.randint(0, 10) for _ in range(n)]
        r = A(beats(*t), mechs(*iv), L(*[(i, i) for i in range(n)]))
        mx, my = Fraction(sum(t), n), Fraction(sum(iv), n)
        sxx = sum((x - mx) ** 2 for x in t)
        syy = sum((y - my) ** 2 for y in iv)
        if sxx == 0 or syy == 0:
            assert r["correlation"] is None
        else:
            want = float(sum((x - mx) * (y - my) for x, y in zip(t, iv))) / math.sqrt(float(sxx) * float(syy))
            assert r["correlation"] == pytest.approx(want, abs=1e-12)
        assert r["mean_abs_gap"] == pytest.approx(sum(abs(x - y) for x, y in zip(t, iv)) / n)


def test_validation():
    ok_b, ok_m = beats(1, 2), mechs(3)
    for bad_b, m in [([], "beats"), ("x", "beats"), ([5], r"beats\[0\]: dict"), ([{"id": "", "tension": 1}], "id must"),
                     ([{"id": "x" * 41, "tension": 1}], "id must"), ([{"id": "a", "tension": True}, {"id": "b", "tension": 1}], "number required"),
                     ([{"id": "a", "tension": "3"}], "number required"), ([{"id": "a", "tension": 11}], r"within \[0, 10\]"),
                     ([{"id": "a", "tension": -1}], r"within \[0, 10\]"), ([{"id": "a", "tension": float("nan")}], "finite"),
                     ([{"id": "a", "tension": float("inf")}], "magnitude"), ([{"id": "a", "tension": 1e10}], "magnitude"),
                     ([{"id": "a", "tension": 1}, {"id": "a", "tension": 2}], "duplicate id")]:
        with pytest.raises(ValueError, match=m):
            A(bad_b, ok_m, [])
    assert A([{"id": "x" * 40, "tension": 10}], ok_m, [])["beats"][0]["tension"] == 10.0
    assert A([{"id": "a", "tension": 0}], ok_m, [])["beats"][0]["tension"] == 0.0
    with pytest.raises(ValueError, match="mechanics"):
        A(ok_b, [], [])
    with pytest.raises(ValueError, match="links"):
        A(ok_b, ok_m, "no")
    with pytest.raises(ValueError, match=r"links\[0\]"):
        A(ok_b, ok_m, [{"beat": "zz", "mechanic": "m0"}])
    with pytest.raises(ValueError, match=r"links\[0\]"):
        A(ok_b, ok_m, [5])
    with pytest.raises(ValueError, match="duplicate link"):
        A(ok_b, ok_m, L((0, 0), (0, 0)))
    for th in [True, "3", -1, 11, float("nan")]:
        with pytest.raises(ValueError, match="threshold"):
            A(ok_b, ok_m, [], th)
    many_b = [{"id": f"b{i}", "tension": 1} for i in range(201)]
    with pytest.raises(ValueError, match="1..200"):
        A(many_b, ok_m, [])
    assert len(A(many_b[:200], ok_m, [])["beats"]) == 200
    many_m = [{"id": f"m{i}", "intensity": 1} for i in range(201)]
    with pytest.raises(ValueError, match="1..200"):
        A(ok_b, many_m, [])
    assert A(ok_b, many_m[:200], [])["unused_mechanics"][:2] == ["m0", "m1"]
    big = [{"id": f"b{i}", "tension": 1} for i in range(200)]
    bm = [{"id": f"m{i}", "intensity": 1} for i in range(200)]
    links = [{"beat": f"b{i}", "mechanic": f"m{j}"} for i in range(5) for j in range(200)]
    assert A(big, bm, links)["coverage"] == 0.025
    with pytest.raises(ValueError, match="at most 1000"):
        A(big, bm, links + [{"beat": "b5", "mechanic": "m0"}])


def test_fractions_and_floats_accepted():
    r = A([{"id": "a", "tension": Fraction(1, 3)}, {"id": "b", "tension": 2.5}], mechs(1), [{"beat": "a", "mechanic": "m0"}])
    assert r["beats"][0]["tension"] == pytest.approx(1 / 3) and r["beats"][1]["tension"] == 2.5


def test_threshold_zero_and_magnitude_boundary():
    r = A(beats(4), mechs(4), L((0, 0)), 0)
    assert r["threshold"] == 0.0 and r["beats"][0]["dissonant"] is True      # |gap| 0 >= 0
    with pytest.raises(ValueError, match=r"within \[0, 10\]"):
        A([{"id": "a", "tension": 1e9}], mechs(1), [])
    with pytest.raises(ValueError, match="magnitude above 1e9"):
        A([{"id": "a", "tension": 1e9 + 1000}], mechs(1), [])
    with pytest.raises(ValueError, match=r"within \[0, 10\]"):
        A(beats(1), mechs(1), [], 5e8)


def test_tiny_and_huge_fraction_inputs_do_not_underflow():
    # auditor finding: float(sxx*syy) underflows for 1/10**100 scale values. Correlation of x with x is exactly +1.
    tiny = [Fraction(i, 10 ** 100) for i in (1, 2, 3)]
    b = [{"id": f"b{i}", "tension": x} for i, x in enumerate(tiny)]
    m = [{"id": f"m{i}", "intensity": x} for i, x in enumerate(tiny)]
    r = A(b, m, L((0, 0), (1, 1), (2, 2)))
    assert r["correlation"] == pytest.approx(1.0, abs=1e-12)
    m2 = [{"id": f"m{i}", "intensity": x} for i, x in enumerate(reversed(tiny))]
    assert A(b, m2, L((0, 0), (1, 1), (2, 2)))["correlation"] == pytest.approx(-1.0, abs=1e-12)
    assert A(b, m, L((0, 0), (1, 1), (2, 2)))["mean_abs_gap"] == 0.0
    # nonzero tiny variance on one side only is still a valid correlation, not None
    mixed = [{"id": f"m{i}", "intensity": x} for i, x in enumerate([Fraction(1), Fraction(2), Fraction(3)])]
    assert A(b, mixed, L((0, 0), (1, 1), (2, 2)))["correlation"] == pytest.approx(1.0, abs=1e-12)


def test_integer_cap_boundaries_then_range():
    with pytest.raises(ValueError, match=r"within \[0, 10\]"):
        A([{"id": "a", "tension": 10 ** 9}], mechs(1), [])
    with pytest.raises(ValueError, match="magnitude above 1e9"):
        A([{"id": "a", "tension": 10 ** 9 + 1}], mechs(1), [])
    with pytest.raises(ValueError, match="magnitude above 1e9"):
        A([{"id": "a", "tension": -(10 ** 9) - 1}], mechs(1), [])
    with pytest.raises(ValueError, match=r"within \[0, 10\]"):
        A([{"id": "a", "tension": -(10 ** 9)}], mechs(1), [])
    with pytest.raises(ValueError, match=r"within \[0, 10\]"):
        A([{"id": "a", "tension": 10.000001}], mechs(1), [])
    assert A([{"id": "a", "tension": 10}], mechs(10), [])["beats"][0]["tension"] == 10.0


def test_correlation_sign_and_clamp_exact():
    r = A(beats(0, 10, 5), mechs(0, 10, 5), L((0, 0), (1, 1), (2, 2)))
    assert r["correlation"] == 1.0                                          # exactly 1 after clamp, not 0.9999999999999999
    r = A(beats(0, 10, 5), mechs(10, 0, 5), L((0, 0), (1, 1), (2, 2)))
    assert r["correlation"] == -1.0


def test_auditor_witness_1e200_correlation_survives_squaring():
    import decimal
    e = Fraction(1, 10 ** 200)
    ys = [Fraction(1), e, 1 + e]
    b = [{"id": f"b{i}", "tension": x} for i, x in enumerate([0, 1, 2])]
    m = [{"id": f"m{i}", "intensity": y} for i, y in enumerate(ys)]
    r = A(b, m, L((0, 0), (1, 1), (2, 2)))
    with decimal.localcontext() as ctx:
        ctx.prec = 80
        ctx.Emin, ctx.Emax = decimal.MIN_EMIN, decimal.MAX_EMAX
        D = decimal.Decimal
        xs = [Fraction(0), Fraction(1), Fraction(2)]
        mx, my = sum(xs) / 3, sum(ys) / 3
        sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
        sxx = sum((x - mx) ** 2 for x in xs)
        syy = sum((y - my) ** 2 for y in ys)
        prod = sxx * syy
        denom = (D(prod.numerator) / D(prod.denominator)).sqrt()
        want = float(D(sxy.numerator) / D(sxy.denominator) / denom)
    assert want > 0 and want == pytest.approx(0.8660254037844386e-200, rel=1e-9, abs=0)
    assert r["correlation"] == pytest.approx(want, rel=1e-9, abs=0)
    # negative orientation keeps the sign
    m2 = [{"id": f"m{i}", "intensity": y} for i, y in enumerate([1 + e, e, Fraction(1)])]
    assert A(b, m2, L((0, 0), (1, 1), (2, 2)))["correlation"] == pytest.approx(-want, rel=1e-9, abs=0)


def test_correlation_below_float_range_rounds_to_zero_not_crash():
    e = Fraction(1, 10 ** 400)
    b = [{"id": f"b{i}", "tension": x} for i, x in enumerate([0, 1, 2])]
    m = [{"id": f"m{i}", "intensity": y} for i, y in enumerate([Fraction(1), e, 1 + e])]
    assert A(b, m, L((0, 0), (1, 1), (2, 2)))["correlation"] == 0.0         # true value ~0.87e-400 is below the float range

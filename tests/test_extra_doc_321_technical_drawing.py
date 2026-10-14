from decimal import Decimal as D
import itertools
import random
import pytest
from sugarcode.extra_doc import technical_drawing as t


def test_constants():
    assert t.MAX_CHAIN == 50 and t.STATUS_NOTE.startswith("PARTIAL")
    assert "no manufacturing or safety claim" in t.STATUS_NOTE


def test_limits_hand():
    assert t.limits(10, 0.1) == {"nominal": D(10), "min": D("9.9"), "max": D("10.1"), "band": D("0.2")}
    assert t.limits("25.4", "0.05", "0.15") == {"nominal": D("25.4"), "min": D("25.25"), "max": D("25.45"), "band": D("0.20")}
    assert t.limits(10, 0.1, 0) == {"nominal": D(10), "min": D("10"), "max": D("10.1"), "band": D("0.1")}
    assert t.limits(-5, 0, 0) == {"nominal": D(-5), "min": D(-5), "max": D(-5), "band": D(0)}
    assert t.limits(0.1 + 0.2, 0) ["min"] == D("0.30000000000000004")


def test_limits_decimal_exactness():
    r = t.limits(0.7, 0.1)
    assert r["max"] == D("0.8") and r["min"] == D("0.6") and r["band"] == D("0.2")
    assert t.limits("1e-3", "1e-3")["min"] == 0


def test_stack_up_hand_rss_exact():
    r = t.stack_up([(10, "0.3", None, 1), (5, "0.4", None, -1)])
    assert r["nominal"] == 5 and r["mid"] == 5
    assert (r["worst_min"], r["worst_max"]) == (D("4.3"), D("5.7"))
    assert (r["rss_min"], r["rss_max"]) == (D("4.5"), D("5.5"))
    assert r["status"] == t.STATUS_NOTE


def test_stack_up_asymmetric_hand():
    r = t.stack_up([(10, "0.1", None, 1), (4, "0.05", "0.15", -1)])
    assert r["nominal"] == 6 and r["mid"] == D("6.05")
    assert (r["worst_min"], r["worst_max"]) == (D("5.85"), D("6.25"))


def test_worst_case_matches_corner_enumeration():
    rnd = random.Random(8)
    for _ in range(80):
        n = rnd.randint(1, 6)
        chain = [(rnd.randint(1, 50), str(rnd.randint(0, 30) / 100), rnd.choice([None, str(rnd.randint(0, 30) / 100)]),
                  rnd.choice([1, -1])) for _ in range(n)]
        best_hi, best_lo = None, None
        spans = []
        for nom, p, m, sg in chain:
            lo, hi = D(nom) - D(m if m is not None else p), D(nom) + D(p)
            spans.append((sg, lo, hi))
        for pick in itertools.product((0, 1), repeat=n):
            v = sum(sg * (lo, hi)[k] for (sg, lo, hi), k in zip(spans, pick))
            best_hi = v if best_hi is None or v > best_hi else best_hi
            best_lo = v if best_lo is None or v < best_lo else best_lo
        r = t.stack_up(chain)
        assert (r["worst_min"], r["worst_max"]) == (best_lo, best_hi)
        half = [float((hi - lo) / 2) for _, lo, hi in spans]
        mid = (best_lo + best_hi) / 2
        rss = sum(h * h for h in half) ** 0.5
        assert float(r["rss_max"] - mid) == pytest.approx(rss, abs=1e-9)
        assert float(mid - r["rss_min"]) == pytest.approx(rss, abs=1e-9)
        assert r["nominal"] == sum(sg * D(nom) for nom, _, _, sg in chain)


def test_fit_classes_hand():
    r = t.fit(10, "0.1", 0, 9.9, 0, "0.1")  # hole [10, 10.1], shaft [9.8, 9.9]
    assert (r["min_clearance"], r["max_clearance"], r["kind"]) == (D("0.1"), D("0.3"), "clearance")
    r = t.fit(10, "0.05", "0.05", 10.1, "0.02", "0.02")  # hole [9.95, 10.05], shaft [10.08, 10.12]
    assert (r["min_clearance"], r["max_clearance"], r["kind"]) == (D("-0.17"), D("-0.03"), "interference")
    r = t.fit(10, "0.1", 0, 10.05, "0.1", "0.1")  # hole [10, 10.1], shaft [9.95, 10.15]
    assert (r["min_clearance"], r["max_clearance"], r["kind"]) == (D("-0.15"), D("0.15"), "transition")
    assert r["status"] == t.STATUS_NOTE


def test_fit_boundaries_are_transition():
    r = t.fit(10, "0.1", 0, 9.9, "0.1", "0.1")  # hole [10, 10.1], shaft [9.8, 10.0]: min clearance exactly 0
    assert r["min_clearance"] == 0 and r["kind"] == "transition"
    r = t.fit(9.9, "0.1", 0, 10.05, "0.05", "0.05")  # hole [9.9, 10.0], shaft [10.0, 10.1]: max clearance exactly 0
    assert r["max_clearance"] == 0 and r["kind"] == "transition"


@pytest.mark.parametrize("args", [
    (True, 0.1), ("abc", 0.1), (None, 0.1), ([1], 0.1), (10, -0.1), (10, 1000.5), (10, True), (10, "x"), (10, 0.1, -1),
    (10, 0.1, 1001), (10, 0.1, True), (1000001, 0.1), (-1000001, 0.1), ("NaN", 0.1), ("Infinity", 0.1),
    (float("nan"), 0.1), (float("inf"), 0.1), (2 * 10 ** 9, 0.1), ("1e400", 0.1),
])
def test_limits_rejects(args):
    with pytest.raises(ValueError):
        t.limits(*args)


def test_limits_edges_and_messages():
    assert t.limits(1000000, 1000)["max"] == 1001000
    assert t.limits(-1000000, 0, 1000)["min"] == -1001000
    with pytest.raises(ValueError, match="nominal: must be within"):
        t.limits(1000001, 0)
    with pytest.raises(ValueError, match="plus: must be within"):
        t.limits(1, 1001)
    with pytest.raises(ValueError, match="minus: must be within"):
        t.limits(1, 1, 1001)
    with pytest.raises(ValueError, match="nominal: number required"):
        t.limits(True, 1)
    with pytest.raises(ValueError, match="nominal: number required"):
        t.limits("abc", 1)
    with pytest.raises(ValueError, match="nominal: finite number required"):
        t.limits("NaN", 1)
    with pytest.raises(ValueError, match="nominal: magnitude above 1e9"):
        t.limits(10 ** 9 + 1, 1)
    with pytest.raises(ValueError, match="nominal: must be within"):
        t.limits(10 ** 9, 1)
    with pytest.raises(ValueError, match="nominal: magnitude above 1e9"):
        t.limits("1000000000.5", 1)


@pytest.mark.parametrize("chain", [
    [], "ab", None, [(1, 0.1, None)], [(1, 0.1, None, 2)], [(1, 0.1, None, 0)], [(1, 0.1, None, True)],
    [(1, 0.1, None, 1.0)], [(1, 0.1, None, "1")], [5], [(1, 0.1, None, 1)] * 51, [(True, 0.1, None, 1)],
])
def test_stack_up_rejects(chain):
    with pytest.raises(ValueError):
        t.stack_up(chain)


def test_stack_up_limits_and_messages():
    assert t.stack_up([(1, 0, None, 1)] * 50)["nominal"] == 50
    assert t.stack_up([(1, 0, None, -1)])["nominal"] == -1
    with pytest.raises(ValueError, match="chain: 1 to 50 required"):
        t.stack_up([])
    with pytest.raises(ValueError, match="link: .* sign 1 or -1 required"):
        t.stack_up([(1, 0, None, 2)])
    with pytest.raises(ValueError, match="plus: must be within"):
        t.stack_up([(1, 2000, None, 1)])


def test_precision_is_50_digits_and_context_not_polluted():
    import decimal
    before = decimal.getcontext().prec
    r = t.stack_up([(1, "1", None, 1), (1, "1", None, 1)])  # half-widths 1 and 1, rss = sqrt(2), mid = 2
    assert r["rss_max"] == D("3.4142135623730950488016887242096980785696718753769")
    assert decimal.getcontext().prec == before == 28
    assert t.limits("1.23456789012345678901", 0)["min"] == D("1.23456789012345678901")


def test_decimal_places_bound_and_exactness():
    assert t.MAX_DECIMAL_PLACES == 20
    ok = "1." + "0" * 19 + "1"          # 20 places
    r = t.limits(ok, 0)
    assert r["min"] == r["max"] == D(ok) and r["nominal"] == D(ok)
    r = t.limits(ok, "0." + "0" * 19 + "1")
    assert r["max"] == D("1.00000000000000000002") and r["min"] == D("1")
    for bad in ["1." + "0" * 59 + "1", "1." + "0" * 20 + "1", "0." + "0" * 20 + "1", "-1." + "0" * 20 + "5"]:
        with pytest.raises(ValueError, match="nominal: more than 20 decimal places"):
            t.limits(bad, 0)
    with pytest.raises(ValueError, match="plus: more than 20 decimal places"):
        t.limits(1, "0." + "0" * 20 + "1")
    with pytest.raises(ValueError, match="minus: more than 20 decimal places"):
        t.limits(1, 0, "0." + "0" * 20 + "1")
    with pytest.raises(ValueError, match="nominal: more than 20 decimal places"):
        t.limits(1e-21, 0)
    assert t.limits(1e-20, 0)["nominal"] == D("1e-20")
    assert t.limits("1." + "0" * 40, 0)["nominal"] == 1      # trailing zeros do not count
    assert t.limits("0." + "0" * 40, 0)["nominal"] == 0
    assert t.limits("1.5e-3", 0)["nominal"] == D("0.0015")
    assert t.limits("1e-20", 0)["min"] == D("1e-20")
    with pytest.raises(ValueError, match="more than 20 decimal places"):
        t.limits("1e-21", 0)
    assert t.limits("12e+3", 0)["nominal"] == 12000


def test_exactness_against_fraction_oracle_at_20_places():
    from fractions import Fraction
    rnd = random.Random(12)
    for _ in range(100):
        n = "%d.%020d" % (rnd.randint(-999, 999), rnd.randint(0, 10 ** 20 - 1))
        p = "0.%020d" % rnd.randint(0, 10 ** 20 - 1)
        m = "0.%020d" % rnd.randint(0, 10 ** 20 - 1)
        r = t.limits(n, p, m)
        fn = Fraction(n)
        assert Fraction(r["max"]) == fn + Fraction(p) and Fraction(r["min"]) == fn - Fraction(m)
        assert Fraction(r["band"]) == Fraction(p) + Fraction(m)
        h = t.fit(n, p, m, n, m, p)
        assert Fraction(h["min_clearance"]) == (fn - Fraction(m)) - (fn + Fraction(m))
        assert Fraction(h["max_clearance"]) == (fn + Fraction(p)) - (fn - Fraction(p))


def test_trailing_zero_boundary_of_decimal_places():
    assert t.limits("0.12345678901234567890" + "0", 0)["nominal"] == D("0.1234567890123456789")   # 21 digits, 19 real
    assert t.limits("0.12345678901234567891" + "0", 0)["nominal"] == D("0.12345678901234567891")  # 22 chars, 20 real
    with pytest.raises(ValueError, match="more than 20 decimal places"):
        t.limits("0.12345678901234567891" + "00" + "1", 0)
    with pytest.raises(ValueError, match="more than 20 decimal places"):
        t.limits("0.123456789012345678901" + "0", 0)      # 22 places, last is zero, 21 real
    with pytest.raises(ValueError, match="more than 20 decimal places"):
        t.limits("0.1234567890123456789010", 0)
    assert t.limits("0.00000000000000000010", 0)["nominal"] == D("1E-19")


def test_two_digit_coefficient_with_trailing_zero_at_boundary():
    assert t.limits("0.000000000000000000010", 0)["nominal"] == D("1E-20")   # 21 places written, 20 real
    with pytest.raises(ValueError, match="more than 20 decimal places"):
        t.limits("0.0000000000000000000010", 0)                               # 22 written, 21 real

import inspect
import random
from fractions import Fraction as F

import pytest
from sugarcode.extra_doc import time_series_forecasting as ts

H = ts.forecast


def test_constants_signature():
    assert (ts.MAX_HISTORY, ts.MAX_ABS, ts.MAX_BPS, ts.MAX_HORIZON) == (200, 10**9, 10000, 24)
    assert ts.STATUS_NOTE.startswith("PARTIAL") and "no promise about the future" in ts.STATUS_NOTE
    assert list(inspect.signature(H).parameters) == ["history", "alpha_bps", "beta_bps", "horizon"]


def test_hand_literals():
    r = H([10, 12, 16], 5000, 5000, 2)     # derived by hand: L 10,T 2 -> (L 12,T 2, err 0) -> (L 15, T 5/2, err 2)
    assert (r["level"], r["trend"]) == (F(15), F(5, 2))
    assert r["forecast"] == [F(35, 2), F(20)]
    assert r["mae"] == F(1) and r["status_note"] == ts.STATUS_NOTE
    r = H([1, 5, 2], 10000, 10000, 1)       # weights 1: level follows data, trend follows level change
    assert (r["level"], r["trend"], r["forecast"], r["mae"]) == (F(2), F(-3), [F(-1)], F(7, 2))
    r = H([0, 10, 0], 1, 1, 1)               # alpha = beta = 1/10000, decimals worked out by hand
    assert r["level"] == F("19.998") and r["trend"] == F("9.9999998")
    assert r["forecast"] == [F("29.9979998")] and r["mae"] == F(10)


def test_straight_line_continued_exactly():
    rnd = random.Random(553)
    for _ in range(200):
        n = rnd.randint(3, 15)
        a, d = rnd.randint(-50, 50), rnd.randint(-9, 9)
        hist = [a + d * t for t in range(n)]
        r = H(hist, rnd.randint(1, 10000), rnd.randint(1, 10000), 5)
        assert r["forecast"] == [F(a + d * (n - 1 + h)) for h in range(1, 6)]
        assert (r["level"], r["trend"], r["mae"]) == (F(a + d * (n - 1)), F(d), 0)


def test_constant_history_and_weight_effect():
    r = H([7, 7, 7, 7], 3000, 3000, 3)
    assert r["forecast"] == [F(7)] * 3 and r["trend"] == 0
    lo = H([0, 0, 0, 100], 1, 5000, 1)
    hi = H([0, 0, 0, 100], 10000, 5000, 1)
    assert hi["level"] == 100 and lo["level"] == F(100 * 1, 10000)          # alpha=1: follow; alpha=1/10000: 0 + 1e-4*100
    assert lo["level"] != hi["level"]


def test_horizon_length_and_order():
    r = H([1, 2, 3], 5000, 5000, 24)
    assert len(r["forecast"]) == 24 and r["forecast"][23] == F(3) + 24 * F(1)
    assert len(H([1, 2, 3], 5000, 5000, 1)["forecast"]) == 1
    r = H([1, 2, 4], 5000, 5000, 3)
    assert r["forecast"] == [r["level"] + h * r["trend"] for h in (1, 2, 3)]


def test_caps_both_sides():
    assert H(list(range(200)), 1, 1, 1)["level"] == 199
    with pytest.raises(ValueError, match=r"^history: 3 to 200 entries required$"):
        H(list(range(201)), 1, 1, 1)
    assert H([1, 2, 3], 1, 1, 1)["level"] is not None
    with pytest.raises(ValueError, match=r"^history: 3 to 200 entries required$"):
        H([1, 2], 1, 1, 1)
    assert H([10**9, -10**9, 10**9], 1, 1, 1)["level"] is not None
    with pytest.raises(ValueError, match=r"^history\[0\]: must be within -1000000000 to 1000000000$"):
        H([10**9 + 1, 0, 0], 1, 1, 1)
    with pytest.raises(ValueError, match=r"^history\[2\]: must be within -1000000000 to 1000000000$"):
        H([0, 0, -(10**9) - 1], 1, 1, 1)
    assert H([1, 2, 3], 10000, 10000, 24)["forecast"][-1] == 27
    for nm in ("alpha_bps", "beta_bps"):
        for bad in (0, 10001, -1):
            a = [bad if nm == "alpha_bps" else 5000, bad if nm == "beta_bps" else 5000]
            with pytest.raises(ValueError, match=rf"^{nm}: must be within 1 to 10000$"):
                H([1, 2, 3], a[0], a[1], 1)
    with pytest.raises(ValueError, match=r"^horizon: must be within 1 to 24$"):
        H([1, 2, 3], 1, 1, 0)
    with pytest.raises(ValueError, match=r"^horizon: must be within 1 to 24$"):
        H([1, 2, 3], 1, 1, 25)


def test_type_refusals_and_order():
    for bad in ("abc", None, 5, {1: 1}):
        with pytest.raises(ValueError, match=r"^history: list required$"):
            H(bad, 1, 1, 1)
    for bad in (True, False, 1.0, "1", None, [1]):
        with pytest.raises(ValueError, match=r"^history\[1\]: integer required$"):
            H([1, bad, 3], 1, 1, 1)
        with pytest.raises(ValueError, match=r"^alpha_bps: integer required$"):
            H([1, 2, 3], bad, 1, 1)
        with pytest.raises(ValueError, match=r"^beta_bps: integer required$"):
            H([1, 2, 3], 1, bad, 1)
        with pytest.raises(ValueError, match=r"^horizon: integer required$"):
            H([1, 2, 3], 1, 1, bad)
    with pytest.raises(ValueError, match=r"^alpha_bps: integer required$"):
        H("bad", True, 0, 0)                  # params before history; alpha first
    with pytest.raises(ValueError, match=r"^beta_bps: integer required$"):
        H("bad", 1, True, 0)
    with pytest.raises(ValueError, match=r"^horizon: integer required$"):
        H("bad", 1, 1, True)
    with pytest.raises(ValueError, match=r"^history\[0\]: integer required$"):
        H([True, 10**30, 0], 1, 1, 1)

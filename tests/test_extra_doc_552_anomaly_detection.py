import inspect
import random
import statistics
from fractions import Fraction as F

import pytest
from sugarcode.extra_doc import anomaly_detection as ad

D = ad.detect


def ol(r):
    return [(o["index"], o["value"], o["side"]) for o in r["outliers"]]


def test_constants_signature():
    assert (ad.MAX_VALUES, ad.MAX_ABS, ad.MAX_K_TENTHS) == (500, 10**9, 100)
    assert ad.STATUS_NOTE.startswith("PARTIAL") and "not proof of an error" in ad.STATUS_NOTE
    sig = inspect.signature(D)
    assert list(sig.parameters) == ["values", "k_tenths"] and sig.parameters["k_tenths"].default == 15


def test_hand_literals():
    r = D([1, 2, 3, 4, 5, 6, 7, 8, 100, -50])
    # sorted -50,1,2,3,4,5,6,7,8,100 ; n=10 ; q1 pos 2.25 -> 2+0.25*(3-2)=9/4 ; q3 pos 6.75 -> 6+.75*(7-6)=27/4
    assert (r["q1"], r["q3"], r["iqr"]) == (F(9, 4), F(27, 4), F(9, 2))
    # fences k=1.5: 9/4 - 27/4 = -9/2 ; 27/4 + 27/4 = 27/2
    assert (r["lower"], r["upper"]) == (F(-9, 2), F(27, 2))
    assert ol(r) == [(8, 100, "high"), (9, -50, "low")]
    assert r["status_note"] == ad.STATUS_NOTE
    r = D([10, 12, 14, 16])           # q1 pos .75 -> 10+.75*2=23/2 ; q3 pos 2.25 -> 14+.25*2=29/2 ; iqr 3
    assert (r["q1"], r["q3"], r["iqr"], r["lower"], r["upper"]) == (F(23, 2), F(29, 2), F(3), F(7), F(19))
    assert r["outliers"] == []
    r = D([0, 0, 0, 0, 5])            # q1=q3=0, iqr 0, fences 0 -> 5 is above
    assert (r["q1"], r["q3"], r["lower"], r["upper"]) == (0, 0, 0, 0) and ol(r) == [(4, 5, "high")]
    r = D([1, 2, 3, 4, 5, 6, 7, 8, 9])   # exact positions: q1=3, q3=7
    assert (r["q1"], r["q3"]) == (3, 7)
    assert all(isinstance(r[k], F) for k in ("q1", "q3", "iqr", "lower", "upper"))


def test_fence_edges_strict():
    r = D([-3, 0, 4, 8, 12], 10)        # n=5: q1 pos 1 -> 0 ; q3 pos 3 -> 8 ; iqr 8 ; k=1 fences -8, 16
    assert (r["lower"], r["upper"]) == (-8, 16)
    assert D([-8, 0, 4, 8, 16], 10)["outliers"] == []              # exactly on fences: not outliers
    assert ol(D([-9, 0, 4, 8, 17], 10)) == [(0, -9, "low"), (4, 17, "high")]
    assert ol(D([-8, 0, 4, 8, 17], 10)) == [(4, 17, "high")]
    assert ol(D([-9, 0, 4, 8, 16], 10)) == [(0, -9, "low")]


def test_oracle_stdlib_quantiles_and_brute_force():
    rnd = random.Random(552)
    for _ in range(300):
        n = rnd.randint(4, 14)
        vals = [rnd.randint(-20, 40) for _ in range(n)]
        kt = rnd.randint(1, 40)
        q1, _, q3 = statistics.quantiles([F(v) for v in vals], n=4, method="inclusive")
        k = F(kt, 10)
        lo, hi = q1 - k * (q3 - q1), q3 + k * (q3 - q1)
        r = D(vals, kt)
        assert (r["q1"], r["q3"], r["lower"], r["upper"]) == (q1, q3, lo, hi)
        want = [(i, v, "low" if v < lo else "high") for i, v in enumerate(vals) if v < lo or v > hi]
        assert ol(r) == want


def test_default_k_is_1_5_and_k_changes_result():
    vals = [1, 2, 3, 4, 5, 6, 7, 8, 100, -50]
    assert D(vals) == D(vals, 15)
    r = D(vals, 100)                                # k=10: 9/4 - 45 = -171/4 ; 27/4 + 45 = 207/4
    assert (r["lower"], r["upper"]) == (F(-171, 4), F(207, 4))
    assert ol(r) == [(8, 100, "high"), (9, -50, "low")]
    assert D([0, 10, 20, 30, 40, 60], 15)["outliers"] == []
    # n=6: q1=25/2, q3=75/2, iqr 25 ; k=0.1 fences 10 and 40 ; k=1.5 fences -25 and 75
    assert ol(D([0, 10, 20, 30, 40, 60], 1)) == [(0, 0, "low"), (5, 60, "high")]


def test_caps_both_sides():
    assert len(D(list(range(500)))["outliers"]) == 0
    with pytest.raises(ValueError, match=r"^values: 4 to 500 entries required$"):
        D(list(range(501)))
    assert D([1, 2, 3, 4])["iqr"] == F(3, 2)
    with pytest.raises(ValueError, match=r"^values: 4 to 500 entries required$"):
        D([1, 2, 3])
    assert D([10**9, -10**9, 0, 1])["q1"] is not None
    with pytest.raises(ValueError, match=r"^values\[0\]: must be within -1000000000 to 1000000000$"):
        D([10**9 + 1, 0, 0, 0])
    with pytest.raises(ValueError, match=r"^values\[3\]: must be within -1000000000 to 1000000000$"):
        D([0, 0, 0, -(10**9) - 1])
    assert D([1, 2, 3, 4], 1)["lower"] == F(7, 4) - F(1, 10) * F(3, 2)
    assert D([1, 2, 3, 4], 100)["lower"] == F(7, 4) - 10 * F(3, 2)
    with pytest.raises(ValueError, match=r"^k_tenths: must be within 1 to 100$"):
        D([1, 2, 3, 4], 0)
    with pytest.raises(ValueError, match=r"^k_tenths: must be within 1 to 100$"):
        D([1, 2, 3, 4], 101)


def test_type_refusals_and_order():
    for bad in ("abcd", None, 5, {1: 1}):
        with pytest.raises(ValueError, match=r"^values: list required$"):
            D(bad)
    for bad in (True, False, 1.0, "1", None, [1]):
        with pytest.raises(ValueError, match=r"^values\[2\]: integer required$"):
            D([1, 2, bad, 4])
        with pytest.raises(ValueError, match=r"^k_tenths: integer required$"):
            D([1, 2, 3, 4], bad)
    with pytest.raises(ValueError, match=r"^k_tenths: integer required$"):
        D("bad", True)                       # k validated before the list
    with pytest.raises(ValueError, match=r"^values\[0\]: integer required$"):
        D([True, 10**30, 0, 0])              # bool before cap

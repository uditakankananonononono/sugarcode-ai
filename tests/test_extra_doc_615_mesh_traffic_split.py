import inspect
import math
import random
from fractions import Fraction as F

import pytest
from sugarcode.extra_doc import mesh_traffic_split as mt

S = mt.split


def cnt(r):
    return [(x["service"], x["requests"]) for x in r["split"]]


def test_constants_signature():
    assert (mt.MAX_REQUESTS, mt.MAX_SERVICES, mt.MAX_NAME, mt.MAX_WEIGHT) == (10**9, 20, 30, 10**6)
    assert mt.STATUS_NOTE.startswith("PARTIAL") and "no real traffic routing" in mt.STATUS_NOTE
    assert list(inspect.signature(S).parameters) == ["requests", "weights"]


def test_hand_literals():
    r = S(100, [("a", 1), ("b", 1), ("c", 1)])
    assert cnt(r) == [("a", 34), ("b", 33), ("c", 33)]            # 33.33 each: leftover 1 goes to the earliest tie
    assert r["total_weight"] == 3 and r["status_note"] == mt.STATUS_NOTE
    assert cnt(S(10, [("a", 90), ("b", 10)])) == [("a", 9), ("b", 1)]
    assert cnt(S(10, [("a", 1), ("b", 2), ("c", 3)])) == [("a", 2), ("b", 3), ("c", 5)]   # 1.67 3.33 5.0: floors 1 3 5, extra to a
    assert cnt(S(0, [("a", 1), ("b", 2)])) == [("a", 0), ("b", 0)]
    assert cnt(S(7, [("a", 0), ("b", 5)])) == [("a", 0), ("b", 7)]
    assert cnt(S(5, [("a", 1), ("b", 1)])) == [("a", 3), ("b", 2)]
    assert cnt(S(5, [("b", 1), ("a", 1)])) == [("b", 3), ("a", 2)]                         # input order breaks ties
    assert cnt(S(2, [("a", 10), ("b", 1), ("c", 1)])) == [("a", 2), ("b", 0), ("c", 0)]   # 1.67, .17, .17 -> a gets the extra
    assert cnt(S(3, [("a", 5), ("b", 3), ("c", 2)])) == [("a", 1), ("b", 1), ("c", 1)]     # 1.5 .9 .6 -> floors 1 0 0, extras to b (.9) then c (.6)
    assert cnt(S(1, [("only", 4)])) == [("only", 1)]
    assert cnt(S(10**9, [("a", 10**6), ("b", 10**6)])) == [("a", 5 * 10**8), ("b", 5 * 10**8)]


def test_oracle_fraction_properties():
    rnd = random.Random(615)
    for _ in range(600):
        n = rnd.randint(1, 6)
        ws = [rnd.randint(0, 6) for _ in range(n)]
        if sum(ws) == 0:
            ws[rnd.randrange(n)] = 1
        req = rnd.randint(0, 40)
        got = [x["requests"] for x in S(req, [(f"s{i}", w) for i, w in enumerate(ws)])["split"]]
        quota = [F(req * w, sum(ws)) for w in ws]
        assert sum(got) == req
        assert all(math.floor(q) <= g <= math.ceil(q) for q, g in zip(quota, got))
        for i in range(n):
            for j in range(n):
                gi, gj = got[i] > math.floor(quota[i]), got[j] == math.floor(quota[j]) and quota[j] != math.floor(quota[j])
                if gi and gj:                                       # i got an extra, j (inexact) did not
                    ri, rj = quota[i] - math.floor(quota[i]), quota[j] - math.floor(quota[j])
                    assert ri > rj or (ri == rj and i < j)


def test_caps_both_sides():
    assert S(10**9, [("a", 1)])["split"][0]["requests"] == 10**9
    with pytest.raises(ValueError, match=r"^requests: must be within 0 to 1000000000$"):
        S(10**9 + 1, [("a", 1)])
    with pytest.raises(ValueError, match=r"^requests: must be within 0 to 1000000000$"):
        S(-1, [("a", 1)])
    ws = [(f"s{i}", 1) for i in range(20)]
    assert len(S(20, ws)["split"]) == 20
    with pytest.raises(ValueError, match=r"^weights: 1 to 20 entries required$"):
        S(1, ws + [("s20", 1)])
    with pytest.raises(ValueError, match=r"^weights: 1 to 20 entries required$"):
        S(1, [])
    assert S(1, [("n" * 30, 1)])["split"][0]["service"] == "n" * 30
    with pytest.raises(ValueError, match=r"^weights\[0\] service: non-empty string up to 30 characters required$"):
        S(1, [("n" * 31, 1)])
    assert S(1, [("a", 10**6)])["total_weight"] == 10**6
    with pytest.raises(ValueError, match=r"^weights\[0\] weight: must be within 0 to 1000000$"):
        S(1, [("a", 10**6 + 1)])
    with pytest.raises(ValueError, match=r"^weights\[1\] weight: must be within 0 to 1000000$"):
        S(1, [("a", 1), ("b", -1)])
    with pytest.raises(ValueError, match=r"^weights: at least one weight above 0 required$"):
        S(1, [("a", 0), ("b", 0)])


def test_type_refusals_and_order():
    for bad in (True, False, 1.0, "1", None):
        with pytest.raises(ValueError, match=r"^requests: integer required$"):
            S(bad, [("a", 1)])
        with pytest.raises(ValueError, match=r"^weights\[0\] weight: integer required$"):
            S(1, [("a", bad)])
    for bad in ("ab", None, 5, {"a": 1}):
        with pytest.raises(ValueError, match=r"^weights: list required$"):
            S(1, bad)
    for bad in ("ab", None, 3):
        with pytest.raises(ValueError, match=r"^weights\[0\]: \(service, weight\) required$"):
            S(1, [bad])
    for bad in [("a",), ("a", 1, 2), ()]:
        with pytest.raises(ValueError, match=r"^weights\[1\]: 2 entries required$"):
            S(1, [("ok", 1), bad])
    for bad in ("", None, 5, True, b"a"):
        with pytest.raises(ValueError, match=r"^weights\[0\] service: non-empty string"):
            S(1, [(bad, 1)])
    with pytest.raises(ValueError, match=r"^weights\[1\] service: duplicate$"):
        S(1, [("a", 1), ("a", 1)])
    with pytest.raises(ValueError, match=r"^requests: integer required$"):
        S(True, "bad")
    with pytest.raises(ValueError, match=r"^weights\[0\] weight: integer required$"):
        S(1, [("a", True), ("b", 10**30)])

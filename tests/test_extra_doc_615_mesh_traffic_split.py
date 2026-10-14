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


# ---- exact-type hardening (v2) ----
import enum


class I(int):
    pass


class LyingI(int):
    """Compares inside every range whatever its value and is never zero or negative-looking."""
    def __ge__(self, o): return True
    def __le__(self, o): return True
    def __gt__(self, o): return True
    def __lt__(self, o): return False
    def __ne__(self, o): return False
    def __eq__(self, o): return True
    __hash__ = int.__hash__


class E(enum.IntEnum):
    ONE = 1
    ZERO = 0


class S_(str):
    pass


class LyingS(str):
    def __eq__(self, o): return False
    def __ne__(self, o): return True
    __hash__ = str.__hash__


class L(list):
    pass


class T(tuple):
    pass


REQ_INT = r"^requests: integer required$"
OK = [("a", 1)]


def _bad(msg, *args):
    with pytest.raises(ValueError, match=msg):
        S(*args)


def test_exact_builtin_list_and_tuple_shapes_accepted():
    assert cnt(S(3, [("a", 1), ["b", 2]])) == [("a", 1), ("b", 2)]
    assert cnt(S(3, (("a", 1), ["b", 2]))) == [("a", 1), ("b", 2)]
    assert cnt(S(0, (("a", 0), ("b", 1)))) == [("a", 0), ("b", 0)]


def test_requests_int_subclasses_refused_before_range_check():
    for bad in (I(5), LyingI(5), LyingI(10**30), I(10**30), I(-1), E.ONE, E.ZERO, True, False):
        _bad(REQ_INT, bad, OK)


def test_weight_int_subclasses_refused_first_and_later_and_before_range_check():
    for bad in (I(1), LyingI(1), LyingI(10**30), I(10**30), E.ONE, E.ZERO, True, False):
        _bad(r"^weights\[0\] weight: integer required$", 1, [("a", bad)])
        _bad(r"^weights\[1\] weight: integer required$", 1, [("a", 1), ("b", bad)])
        _bad(r"^weights\[2\] weight: integer required$", 1, [("a", 1), ("b", 1), ("c", bad)])


def test_weights_list_and_tuple_subclasses_refused():
    for K in (L, T):
        _bad(r"^weights: list required$", 1, K(OK))
        _bad(r"^weights: list required$", 1, K())
    _bad(r"^weights: list required$", 1, L(OK * 21))          # subclass refused before the 1 to 20 cap


def test_row_list_and_tuple_subclasses_refused_first_and_later():
    for K in (L, T):
        _bad(r"^weights\[0\]: \(service, weight\) required$", 1, [K(("a", 1))])
        _bad(r"^weights\[1\]: \(service, weight\) required$", 1, [("a", 1), K(("b", 1))])
        _bad(r"^weights\[0\]: \(service, weight\) required$", 1, [K(("a",)), ("b", 1)])


def test_service_str_subclasses_refused_first_and_later():
    msg = r"^weights\[%d\] service: non-empty string up to 30 characters required$"
    for bad in (S_("a"), LyingS("a"), LyingS("")):
        _bad(msg % 0, 1, [(bad, 1)])
        _bad(msg % 1, 1, [("a", 1), (bad, 1)])
    _bad(msg % 1, 1, [("a", 1), (S_("a"), 1)])               # not reported as a duplicate


def test_service_boundaries_and_remaining_full_messages():
    msg = r"^weights\[0\] service: non-empty string up to 30 characters required$"
    assert cnt(S(1, [("x", 1)])) == [("x", 1)]
    assert cnt(S(1, [("n" * 30, 1)])) == [("n" * 30, 1)]
    for bad in ("", "n" * 31):
        _bad(msg, 1, [(bad, 1)])
    assert cnt(S(0, [("a", 0), ("b", 1)])) == [("a", 0), ("b", 0)]
    assert cnt(S(0, [("a", 10**6)])) == [("a", 0)]
    _bad(r"^weights\[2\] service: duplicate$", 1, [("a", 1), ("b", 1), ("a", 1)])
    _bad(r"^weights\[0\]: 2 entries required$", 1, [("a",)])
    _bad(r"^weights\[0\]: 2 entries required$", 1, [("a", 1, 1)])
    _bad(r"^weights\[1\] weight: must be within 0 to 1000000$", 1, [("a", 1), ("b", 10**6 + 1)])
    _bad(REQ_INT, "1", OK)


def test_order_requests_checked_before_weights_and_rows_before_total():
    _bad(REQ_INT, I(1), L(OK))
    _bad(r"^weights: list required$", 1, L(OK))
    _bad(r"^weights\[0\] weight: integer required$", 1, [("a", I(0)), ("b", 0)])   # before the zero-total check

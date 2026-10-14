import inspect
import random

import pytest
from sugarcode.extra_doc import fraud_detection as fd

S = fd.screen


def fl(r):
    return [(x["index"], x["rules"]) for x in r["flagged"]]


def test_constants_signature():
    assert (fd.MAX_TX, fd.MAX_TS, fd.MAX_AMOUNT, fd.MAX_COUNT, fd.MAX_WINDOW) == (500, 10**12, 10**9, 100, 86400)
    assert fd.STATUS_NOTE.startswith("PARTIAL") and "not a finding of fraud" in fd.STATUS_NOTE
    assert list(inspect.signature(S).parameters) == ["transactions", "amount_limit", "max_count", "window"]


def test_hand_literals():
    tx = [(0, 100), (10, 5000), (20, 100), (30, 100), (100, 100), (100, 7000)]
    r = S(tx, 4999, 2, 25)
    # large: idx1 (5000>4999), idx5 (7000). burst, window (ts-25, ts]: idx0:{0}=1; idx1:{0,10}=2; idx2:{0?no 0>-5 yes,10,20}=3 -> burst
    # idx3 (5,30]: {10,20,30}=3 -> burst; idx4 (75,100]: {100,100}=2; idx5: 2
    assert fl(r) == [(1, ["large"]), (2, ["burst"]), (3, ["burst"]), (5, ["large"])]
    assert r["checked"] == 6 and r["status_note"] == fd.STATUS_NOTE
    assert r["flagged"][0] == {"index": 1, "ts": 10, "amount": 5000, "rules": ["large"]}
    both = S([(5, 10), (5, 10), (5, 900)], 500, 2, 1)
    assert fl(both) == [(0, ["burst"]), (1, ["burst"]), (2, ["large", "burst"])]
    assert S([(0, 5)], 5, 1, 1)["flagged"] == []          # amount == limit and count == max are not flagged
    assert fl(S([(0, 6)], 5, 1, 1)) == [(0, ["large"])]
    assert S([(0, 0), (1, 0)], 1, 2, 10)["flagged"] == []
    assert fl(S([(0, 0), (1, 0)], 1, 1, 10)) == [(1, ["burst"])]


def test_window_edges():
    # window 10: tx at 0 is outside (10-10, 10] = (0,10]; tx at 1 is inside
    assert S([(0, 1), (10, 1)], 99, 1, 10)["flagged"] == []
    assert fl(S([(1, 1), (10, 1)], 99, 1, 10)) == [(1, ["burst"])]
    assert fl(S([(0, 1), (10, 1)], 99, 1, 11)) == [(1, ["burst"])]


def test_oracle_random_brute_force():
    rnd = random.Random(551)
    for _ in range(400):
        n = rnd.randint(1, 15)
        ts = sorted(rnd.randint(0, 30) for _ in range(n))
        am = [rnd.randint(0, 20) for _ in range(n)]
        lim, mc, w = rnd.randint(1, 20), rnd.randint(1, 5), rnd.randint(1, 12)
        want = []
        for i in range(n):
            rules = []
            if am[i] > lim:
                rules.append("large")
            if sum(1 for j in range(n) if ts[i] - w < ts[j] <= ts[i]) > mc:
                rules.append("burst")
            if rules:
                want.append((i, rules))
        assert fl(S(list(zip(ts, am)), lim, mc, w)) == want


def test_caps_both_sides():
    big = [(i, 1) for i in range(500)]
    assert S(big, 1, 1, 1)["checked"] == 500
    with pytest.raises(ValueError, match=r"^transactions: 1 to 500 entries required$"):
        S(big + [(500, 1)], 1, 1, 1)
    with pytest.raises(ValueError, match=r"^transactions: 1 to 500 entries required$"):
        S([], 1, 1, 1)
    assert S([(10**12, 10**9)], 10**9, 100, 86400)["flagged"] == []
    with pytest.raises(ValueError, match=r"^transactions\[0\] ts: must be within 0 to 1000000000000$"):
        S([(10**12 + 1, 1)], 1, 1, 1)
    with pytest.raises(ValueError, match=r"^transactions\[0\] ts: must be within 0 to 1000000000000$"):
        S([(-1, 1)], 1, 1, 1)
    with pytest.raises(ValueError, match=r"^transactions\[0\] amount: must be within 0 to 1000000000$"):
        S([(0, 10**9 + 1)], 1, 1, 1)
    with pytest.raises(ValueError, match=r"^transactions\[0\] amount: must be within 0 to 1000000000$"):
        S([(0, -1)], 1, 1, 1)
    assert S([(0, 0)], 1, 100, 1)["checked"] == 1
    assert S([(0, 1)], 1, 1, 86400)["checked"] == 1 and S([(0, 1)], 10**9, 1, 1)["checked"] == 1
    with pytest.raises(ValueError, match=r"^amount_limit: must be within 1 to 1000000000$"):
        S([(0, 1)], 0, 1, 1)
    with pytest.raises(ValueError, match=r"^amount_limit: must be within 1 to 1000000000$"):
        S([(0, 1)], 10**9 + 1, 1, 1)
    with pytest.raises(ValueError, match=r"^max_count: must be within 1 to 100$"):
        S([(0, 1)], 1, 0, 1)
    with pytest.raises(ValueError, match=r"^max_count: must be within 1 to 100$"):
        S([(0, 1)], 1, 101, 1)
    with pytest.raises(ValueError, match=r"^window: must be within 1 to 86400$"):
        S([(0, 1)], 1, 1, 0)
    with pytest.raises(ValueError, match=r"^window: must be within 1 to 86400$"):
        S([(0, 1)], 1, 1, 86401)


def test_type_refusals_and_order():
    for bad in ("ab", None, 5, {"a": 1}):
        with pytest.raises(ValueError, match=r"^transactions: list required$"):
            S(bad, 1, 1, 1)
    for bad in ("ab", None, 3):
        with pytest.raises(ValueError, match=r"^transactions\[0\]: \(ts, amount\) required$"):
            S([bad], 1, 1, 1)
    for bad in [(1,), (1, 2, 3), ()]:
        with pytest.raises(ValueError, match=r"^transactions\[1\]: 2 entries required$"):
            S([(0, 1), bad], 1, 1, 1)
    for bad in (True, 1.0, "1", None):
        with pytest.raises(ValueError, match=r"^transactions\[0\] ts: integer required$"):
            S([(bad, 1)], 1, 1, 1)
        with pytest.raises(ValueError, match=r"^transactions\[0\] amount: integer required$"):
            S([(0, bad)], 1, 1, 1)
        with pytest.raises(ValueError, match=r"^amount_limit: integer required$"):
            S([(0, 1)], bad, 1, 1)
        with pytest.raises(ValueError, match=r"^max_count: integer required$"):
            S([(0, 1)], 1, bad, 1)
        with pytest.raises(ValueError, match=r"^window: integer required$"):
            S([(0, 1)], 1, 1, bad)
    with pytest.raises(ValueError, match=r"^transactions\[1\] ts: must not decrease$"):
        S([(5, 1), (4, 1)], 1, 1, 1)
    assert S([(5, 1), (5, 1)], 1, 2, 1)["checked"] == 2      # equal ts is allowed
    with pytest.raises(ValueError, match=r"^amount_limit: integer required$"):
        S("bad", True, 1, 1)                                   # params validated before the list
    with pytest.raises(ValueError, match=r"^transactions\[0\] ts: integer required$"):
        S([(True, 10**30)], 1, 1, 1)

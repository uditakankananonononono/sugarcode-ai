import inspect
import random

import pytest
from sugarcode.extra_doc import ranking_system as rs

R = rs.rank


def rows(r):
    return [(x["name"], x["score"], x["rank"], x["dense_rank"]) for x in r["ranking"]]


def test_constants_and_note():
    assert (rs.MAX_ITEMS, rs.MAX_NAME, rs.MAX_SCORE) == (200, 40, 10**9)
    assert rs.STATUS_NOTE.startswith("PARTIAL") and "no judgment of whether the scores" in rs.STATUS_NOTE
    assert list(inspect.signature(R).parameters) == ["items"]


def test_hand_literals():
    r = R([("d", 5), ("b", 9), ("a", 9), ("c", 7), ("e", 5), ("f", 1)])
    assert rows(r) == [("a", 9, 1, 1), ("b", 9, 1, 1), ("c", 7, 3, 2), ("d", 5, 4, 3), ("e", 5, 4, 3), ("f", 1, 6, 4)]
    assert r["status_note"] == rs.STATUS_NOTE
    assert rows(R([("x", -3)])) == [("x", -3, 1, 1)]
    assert rows(R([("b", 2), ("a", 2), ("c", 2)])) == [("a", 2, 1, 1), ("b", 2, 1, 1), ("c", 2, 1, 1)]
    assert rows(R([("n", -5), ("m", 0), ("p", -5)])) == [("m", 0, 1, 1), ("n", -5, 2, 2), ("p", -5, 2, 2)]
    assert rows(R((("B", 1), ("a", 1)))) == [("B", 1, 1, 1), ("a", 1, 1, 1)]   # code-point order: upper before lower


def test_tie_order_name_not_input_order():
    assert [x["name"] for x in R([("zed", 4), ("amy", 4), ("mid", 4)])["ranking"]] == ["amy", "mid", "zed"]
    assert [x["name"] for x in R([("amy", 4), ("zed", 4)])["ranking"]] == ["amy", "zed"]
    assert [x["name"] for x in R([("zed", 4), ("amy", 4)])["ranking"]] == ["amy", "zed"]


def test_oracle_random_brute_force():
    rnd = random.Random(550)
    for _ in range(300):
        n = rnd.randint(1, 12)
        names = rnd.sample("abcdefghijklmnop", n)
        sc = [rnd.randint(-3, 3) for _ in names]
        out = R(list(zip(names, sc)))["ranking"]
        assert len(out) == n
        for x in out:
            assert x["rank"] == 1 + sum(1 for s in sc if s > x["score"])
            assert x["dense_rank"] == 1 + len({s for s in sc if s > x["score"]})
        keys = [(-x["score"], x["name"]) for x in out]
        assert keys == sorted(keys)
        assert sorted(x["name"] for x in out) == sorted(names)


def test_caps_both_sides():
    ok = [(f"n{i}", i) for i in range(200)]
    assert len(R(ok)["ranking"]) == 200
    with pytest.raises(ValueError, match=r"^items: 1 to 200 entries required$"):
        R(ok + [("extra", 1)])
    with pytest.raises(ValueError, match=r"^items: 1 to 200 entries required$"):
        R([])
    assert R([("a" * 40, 1)])["ranking"][0]["name"] == "a" * 40
    with pytest.raises(ValueError, match=r"^items\[0\] name: non-empty string up to 40 characters required$"):
        R([("a" * 41, 1)])
    assert R([("a", 10**9)])["ranking"][0]["score"] == 10**9
    assert R([("a", -(10**9))])["ranking"][0]["score"] == -(10**9)
    with pytest.raises(ValueError, match=r"^items\[0\] score: must be within -1000000000 to 1000000000$"):
        R([("a", 10**9 + 1)])
    with pytest.raises(ValueError, match=r"^items\[1\] score: must be within -1000000000 to 1000000000$"):
        R([("a", 1), ("b", -(10**9) - 1)])


def test_type_refusals():
    for bad in ("abc", None, 5, {"a": 1}):
        with pytest.raises(ValueError, match=r"^items: list required$"):
            R(bad)
    for bad in ("ab", None, 3, 1.5):
        with pytest.raises(ValueError, match=r"^items\[0\]: \(name, score\) required$"):
            R([bad])
    for bad in [("a",), ("a", 1, 2), ()]:
        with pytest.raises(ValueError, match=r"^items\[1\]: 2 entries required$"):
            R([("ok", 1), bad])
    for bad in ("", None, 5, True, b"a", ["a"]):
        with pytest.raises(ValueError, match=r"^items\[0\] name: non-empty string"):
            R([(bad, 1)])
    for bad in (True, False, 1.0, "1", None, [1]):
        with pytest.raises(ValueError, match=r"^items\[0\] score: integer required$"):
            R([("a", bad)])
    with pytest.raises(ValueError, match=r"^items\[2\] name: duplicate$"):
        R([("a", 1), ("b", 2), ("a", 3)])
    with pytest.raises(ValueError, match=r"^items\[0\] score: integer required$"):
        R([("a", float("nan"))])


def test_validation_order_bool_before_cap():
    with pytest.raises(ValueError, match="integer required"):
        R([("a", True)])
    with pytest.raises(ValueError, match=r"^items\[0\] score: must be within"):
        R([("a", 10**30)])
    with pytest.raises(ValueError, match=r"^items\[1\] name: duplicate$"):
        R([("a", 1), ("a", 10**9)])

import copy
import random
from fractions import Fraction as F

import pytest

from sugarcode.extra_doc import mood_shift as m
from sugarcode.extra_doc.mood_shift import MoodError, mood_shift as run

KEYS = "data keys must be exactly entries"
EK = "entry keys must be exactly after, before, strategy"
SN = "strategy must be 1..12 characters from a-z and _"


def e(s, b, a):
    return {"strategy": s, "before": b, "after": a}


def d(*ents):
    return {"entries": list(ents)}


def bad(data, msg):
    with pytest.raises(MoodError) as x:
        run(data)
    assert str(x.value) == msg


def oracle_row(rows):
    n = len(rows)
    tot = sum(a for _, a in rows) - sum(b for b, _ in rows)
    lt = sum(a < b for b, a in rows)
    eq = sum(a == b for b, a in rows)
    gt = sum(a > b for b, a in rows)
    return {"entries": n, "mean_change": F(tot, n), "went_down": lt, "stayed_equal": eq, "went_up": gt}


def check(data):
    o = run(data)
    groups = {}
    for x in data["entries"]:
        groups.setdefault(x["strategy"], []).append((x["before"], x["after"]))
    assert list(o["strategies"]) == sorted(groups)
    for s, rows in groups.items():
        r = dict(o["strategies"][s])
        r["mean_change"] = F(r["mean_change"])
        assert r == oracle_row(rows)
    allr = [(x["before"], x["after"]) for x in data["entries"]]
    r = dict(o["overall"])
    r["mean_change"] = F(r["mean_change"])
    assert r == oracle_row(allr)
    return o


def test_hand_worked():
    o = run(d(e("walk", 8, 5), e("walk", 6, 6), e("breathe", 4, 6), e("walk", 7, 4)))
    assert list(o["strategies"]) == ["breathe", "walk"]
    assert o["strategies"]["walk"] == {"entries": 3, "mean_change": "-2", "went_down": 2, "stayed_equal": 1, "went_up": 0}
    assert o["strategies"]["breathe"] == {"entries": 1, "mean_change": "2", "went_down": 0, "stayed_equal": 0, "went_up": 1}
    assert o["overall"] == {"entries": 4, "mean_change": "-1", "went_down": 2, "stayed_equal": 1, "went_up": 1}
    assert o["status"] == "completed"
    assert o["claims"] == {"accurate_ratings": False, "causal": False, "generalises": False, "health_claim": False}
    assert len(o["not_claimed"]) == 4
    assert run(d(e("a", 0, 1), e("a", 0, 0)))["strategies"]["a"]["mean_change"] == "1/2"
    assert run(d(e("a", 10, 0)))["overall"]["mean_change"] == "-10"


def test_random():
    rng = random.Random(803)
    names = ["a", "b_c", "zz", "x" * 12, "_"]
    for _ in range(400):
        check(d(*[e(rng.choice(names), rng.randint(0, 10), rng.randint(0, 10)) for _ in range(rng.randint(1, 15))]))


def test_caps():
    run(d(*[e("a", 10, 0)] * 300))
    bad(d(*[e("a", 1, 1)] * 301), "entries must be a list of 1..300 entries")
    bad(d(*[e("a", 1, 1)] * 10**5), "entries must be a list of 1..300 entries")
    bad(d(), "entries must be a list of 1..300 entries")
    ten = [e(c, 1, 1) for c in "abcdefghij"]
    run(d(*ten))
    bad(d(*ten, e("k", 1, 1)), "at most 10 distinct strategies")
    run(d(*ten, e("a", 2, 2)))
    bad(d(e("a", 11, 0)), "before out of range")
    bad(d(e("a", -1, 0)), "before out of range")
    bad(d(e("a", 0, 11)), "after out of range")
    bad(d(e("a", 0, -1)), "after out of range")
    run(d(e("a", 0, 10)))
    run(d(e("a", 10, 0)))


@pytest.mark.parametrize("v", [True, False, 1.0, 1.5, None, "1", [1], {}])
def test_nonint(v):
    bad(d(e("a", v, 1)), "before must be an int")
    bad(d(e("a", 1, v)), "after must be an int")


@pytest.mark.parametrize("s", ["", "A", "a1", "a-b", "a b", "a" * 13, "é", "a\n", None, 1, True, ["a"]])
def test_bad_strategy(s):
    bad(d(e(s, 1, 1)), SN)


@pytest.mark.parametrize("s", ["a", "z", "_", "a" * 12])
def test_good_strategy(s):
    check(d(e(s, 1, 2)))


@pytest.mark.parametrize("v", [True, False, 1, 1.5, None, "ab", {}, ("a",)])
def test_noncontainer(v):
    x = {"entries": v}
    bad(x, "entries must be a list of 1..300 entries")
    bad({"entries": [v]}, EK)


def test_entry_keys_exact():
    bad(d({"strategy": "a", "before": 1}), EK)
    bad(d({"strategy": "a", "after": 1}), EK)
    bad(d({"before": 1, "after": 1}), EK)
    bad(d({"strategy": "a", "before": 1, "after": 1, "x": 1}), EK)


@pytest.mark.parametrize("x", [None, 1, "a", [], True, [("entries", 1)]])
def test_data_not_dict(x):
    bad(x, KEYS)


def test_keys_exact():
    bad({}, KEYS)
    bad({"entries": [e("a", 1, 1)], "x": 1}, KEYS)


def test_no_mutation_determinism_fresh_claims():
    x = d(e("a", 1, 2), e("b", 3, 1))
    y = copy.deepcopy(x)
    a, b = run(x), run(x)
    assert x == y and a == b
    a["claims"]["health_claim"] = True
    a["strategies"]["a"]["entries"] = 9
    r = run(x)
    assert r["claims"]["health_claim"] is False and r["strategies"]["a"]["entries"] == 1 and m.CLAIMS["health_claim"] is False


class _SubInt(int):
    pass


class _Quirky(int):
    """int subclass with lying arithmetic and comparisons."""
    def __sub__(self, o):
        return 0

    def __add__(self, o):
        return 1

    def __mul__(self, o):
        return 0

    def __gt__(self, o):
        return False

    def __lt__(self, o):
        return False


def _int_paths(x, path=()):
    if type(x) is int:
        yield path
    elif isinstance(x, dict):
        for k in x:
            yield from _int_paths(x[k], path + (k,))
    elif isinstance(x, list):
        for i, v in enumerate(x):
            yield from _int_paths(v, path + (i,))


def _put(x, path, val):
    y = copy.deepcopy(x)
    t = y
    for k in path[:-1]:
        t = t[k]
    t[path[-1]] = val
    return y


def test_int_subclasses_refused_in_every_int_slot():
    base = d(e("a", 1, 2), e("b", 3, 1))
    paths = list(_int_paths(base))
    assert paths
    for p in paths:
        for cls in (_SubInt, _Quirky):
            with pytest.raises(MoodError) as exc:
                run(_put(base, p, cls(_get(base, p))))
            assert "must be an int" in str(exc.value) or "must be ints" in str(exc.value)


def _get(x, path):
    for k in path:
        x = x[k]
    return x


class _SubStr(str):
    pass


class _LyingStr(str):
    """str subclass that hashes like 1 and equals 1."""
    def __hash__(self):
        return 1

    def __eq__(self, o):
        return o == 1 or str.__eq__(self, o)


def _variants(x):
    """Yield every copy of x with one str leaf or one dict key replaced by bytes or a str subclass."""
    import copy as _c
    def walk(node, path):
        if type(node) is str:
            yield path, "leaf"
        elif isinstance(node, dict):
            for k in node:
                if type(k) is str:
                    yield path + (k,), "key"
                yield from walk(node[k], path + (k,))
        elif isinstance(node, list):
            for i, v in enumerate(node):
                yield from walk(v, path + (i,))
    for path, kind in walk(x, ()):
        for mk in (lambda s: s.encode(), _SubStr, _LyingStr):
            if kind == "key" and mk is _SubStr:
                continue   # a plain str subclass hashes and compares like its key: indistinguishable as a dict key
            y = _c.deepcopy(x)
            t = y
            for k in path[:-1]:
                t = t[k]
            last = path[-1]
            if kind == "leaf":
                t[last] = mk(t[last])
            else:
                t2 = {}
                for k, v in t.items():
                    t2[mk(k) if k == last else k] = v
                if len(path) == 1:
                    y = t2
                else:
                    u = y
                    for k in path[:-2]:
                        u = u[k]
                    u[path[-2]] = t2
            yield y


def test_nonexact_str_refused_in_every_str_slot_and_key():
    base = d(e("a", 1, 2), e("b", 3, 1))
    n = 0
    for y in _variants(base):
        n += 1
        with pytest.raises(MoodError):
            run(y)
    assert n >= 4

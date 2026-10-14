import copy
import random
from fractions import Fraction as F

import pytest

from sugarcode.extra_doc import coping_tally as m
from sugarcode.extra_doc.coping_tally import CopingError, coping_tally as run

KEYS = "data keys must be exactly attempts"
AT = "attempts must be a list of 1..300 [strategy, worked] pairs"
SN = "strategy must be 1..12 characters from a-z and _"


def d(*a):
    return {"attempts": [list(x) for x in a]}


def bad(data, msg):
    with pytest.raises(CopingError) as e:
        run(data)
    assert str(e.value) == msg


def check(data):
    """Independent: build the ranking with sorted() on an explicit key and take the first."""
    o = run(data)
    names = sorted({s for s, _ in data["attempts"]})
    info = {s: [w for t, w in data["attempts"] if t == s] for s in names}
    assert list(o["strategies"]) == names
    for s in names:
        assert o["strategies"][s] == {"attempts": len(info[s]), "worked": sum(info[s]), "share": str(F(sum(info[s]), len(info[s])))}
    el = [s for s in names if len(info[s]) >= 2]
    exp = sorted(el, key=lambda s: (-F(sum(info[s]), len(info[s])), -len(info[s]), s))
    assert o["top"] == (exp[0] if exp else None)
    return o


def test_hand_worked():
    o = run(d(("walk", 1), ("walk", 0), ("walk", 1), ("tea", 1), ("nap", 1), ("nap", 1)))
    assert o["strategies"]["walk"] == {"attempts": 3, "worked": 2, "share": "2/3"}
    assert o["strategies"]["tea"] == {"attempts": 1, "worked": 1, "share": "1"}
    assert o["top"] == "nap"            # tea has 1 share 1 but only 1 attempt; nap 2/2 beats walk 2/3
    assert list(o["strategies"]) == ["nap", "tea", "walk"]
    assert o["status"] == "completed"
    assert o["claims"] == {"accurate_log": False, "causal": False, "best_for_person": False, "health_claim": False}
    assert len(o["not_claimed"]) == 4


def test_top_rules():
    assert check(d(("a", 1), ("b", 1)))["top"] is None
    assert check(d(("b", 1), ("b", 0), ("a", 1), ("a", 0)))["top"] == "a"                      # tie on share and count: alphabetical
    assert check(d(("b", 1), ("b", 1), ("b", 0), ("b", 0), ("a", 1), ("a", 0)))["top"] == "b"  # equal 1/2, more attempts wins
    assert check(d(("a", 1), ("a", 0), ("b", 1), ("b", 1), ("b", 1), ("b", 0)))["top"] == "b"
    assert check(d(("z", 1), ("z", 1), ("a", 1), ("a", 1)))["top"] == "a"
    assert check(d(("a", 0), ("a", 0)))["top"] == "a"
    assert check(d(("a", 1), ("a", 1), ("b", 1), ("b", 1), ("b", 1)))["top"] == "b"            # share 1 both, 3 > 2


def test_random():
    rng = random.Random(805)
    names = ["a", "b", "c", "zz", "_"]
    for _ in range(500):
        check(d(*[(rng.choice(names), rng.randint(0, 1)) for _ in range(rng.randint(1, 14))]))


def test_caps():
    run(d(*[("a", 1)] * 300))
    bad(d(*[("a", 1)] * 301), AT)
    bad(d(*[("a", 1)] * 10**5), AT)
    bad(d(), AT)
    ten = [(c, 1) for c in "abcdefghij"]
    run(d(*ten))
    bad(d(*ten, ("k", 1)), "at most 10 distinct strategies")
    run(d(*ten, ("a", 0)))
    bad(d(("a", 2)), "worked must be 0 or 1")
    bad(d(("a", -1)), "worked must be 0 or 1")


@pytest.mark.parametrize("v", [True, False, 1.0, 0.0, None, "1", [1], {}])
def test_nonint(v):
    bad({"attempts": [["a", v]]}, "worked must be an int")


@pytest.mark.parametrize("s", ["", "A", "a1", "a-b", "a b", "a" * 13, "é", "a\n", None, 1, True, ["a"]])
def test_bad_strategy(s):
    bad({"attempts": [[s, 1]]}, SN)


@pytest.mark.parametrize("s", ["a", "z", "_", "a" * 12])
def test_good_strategy(s):
    check(d((s, 1), (s, 0)))


@pytest.mark.parametrize("v", [True, False, 1, 1.5, None, "ab", {}, ("a",)])
def test_noncontainer(v):
    bad({"attempts": v}, AT)
    bad({"attempts": [v]}, "attempt must be a [strategy, worked] pair")
    for p in (["a"], ["a", 1, 1]):
        bad({"attempts": [p]}, "attempt must be a [strategy, worked] pair")


@pytest.mark.parametrize("x", [None, 1, "a", [], True, [("attempts", 1)]])
def test_data_not_dict(x):
    bad(x, KEYS)


def test_keys_exact():
    bad({}, KEYS)
    bad({"attempts": [["a", 1]], "x": 1}, KEYS)


def test_no_mutation_determinism_fresh_claims():
    x = d(("a", 1), ("a", 0))
    y = copy.deepcopy(x)
    a, b = run(x), run(x)
    assert x == y and a == b
    a["claims"]["health_claim"] = True
    a["strategies"]["a"]["attempts"] = 9
    r = run(x)
    assert r["claims"]["health_claim"] is False and r["strategies"]["a"]["attempts"] == 2 and m.CLAIMS["health_claim"] is False


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
    base = d(("a", 1), ("a", 0))
    paths = list(_int_paths(base))
    assert paths
    for p in paths:
        for cls in (_SubInt, _Quirky):
            with pytest.raises(CopingError) as e:
                run(_put(base, p, cls(_get(base, p))))
            assert "must be an int" in str(e.value) or "must be ints" in str(e.value)


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
    base = d(("a", 1), ("a", 0))
    n = 0
    for y in _variants(base):
        n += 1
        with pytest.raises(CopingError):
            run(y)
    assert n >= 4

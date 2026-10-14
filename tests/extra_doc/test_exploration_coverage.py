import copy
import random
from fractions import Fraction as F

import pytest

from sugarcode.extra_doc import exploration_coverage as m
from sugarcode.extra_doc.exploration_coverage import ExplorationError, exploration_coverage as run

KEYS = "data keys must be exactly items, visits"
NV = "visits must be a list of 1 to 16 visits"


def d(items=5, visits=(0, 1, 1, 2, 0, 3)):
    return {"items": items, "visits": list(visits)}


def bad(data, msg):
    with pytest.raises(ExplorationError) as e:
        run(data)
    assert str(e.value) == msg


def oracle(x):
    """Independent: list.index for first visits, runs by splitting on repeats."""
    n, v = x["items"], x["visits"]
    first = [(v.index(k) if k in v else None) for k in range(n)]
    isnew = [v.index(val) == i for i, val in enumerate(v)]
    best, cur = 0, 0
    for f in isnew:
        if f:
            cur += 1
            best = max(best, cur)
        else:
            cur = 0
    distinct = len(set(v))
    return first, distinct, F(distinct, n), len(v) - distinct, best, [k for k in range(n) if k not in v]


def check(x):
    o = run(x)
    first, distinct, cov, rev, best, un = oracle(x)
    assert (o["first_visit"], o["distinct"], F(o["coverage"]), o["revisits"], o["longest_new_run"], o["unvisited"]) == (first, distinct, cov, rev, best, un)
    return o


def test_hand_worked():
    o = run(d())
    assert o["first_visit"] == [0, 1, 3, 5, None] and o["distinct"] == 4 and o["coverage"] == "4/5"
    assert o["revisits"] == 2 and o["longest_new_run"] == 2 and o["unvisited"] == [4]
    assert o["status"] == "completed"
    assert o["claims"] == {"happened": False, "coverage_is_discovery": False, "revisits_wasted": False, "real_world": False}
    assert len(o["not_claimed"]) == 4
    check(d())


def test_cases():
    o = run(d(2, [1]))
    assert o["first_visit"] == [None, 0] and o["coverage"] == "1/2" and o["unvisited"] == [0] and o["longest_new_run"] == 1
    o = run(d(3, [0, 1, 2]))
    assert o["longest_new_run"] == 3 and o["revisits"] == 0 and o["coverage"] == "1" and o["unvisited"] == []
    o = run(d(3, [0, 0, 0]))
    assert o["longest_new_run"] == 1 and o["revisits"] == 2 and o["first_visit"] == [0, None, None]
    o = run(d(4, [0, 1, 0, 2, 3]))
    assert o["longest_new_run"] == 2  # visits 3 and 4 (2 then 3) after the revisit
    o = run(d(4, [0, 1, 2, 2, 3]))
    assert o["longest_new_run"] == 3
    o = run(d(10, [9, 0]))
    assert o["first_visit"][9] == 0 and o["first_visit"][0] == 1 and o["coverage"] == "1/5"


def test_random():
    rng = random.Random(903)
    for _ in range(500):
        n = rng.randint(2, 10)
        check(d(n, [rng.randrange(n) for _ in range(rng.randint(1, 16))]))


def test_caps():
    run(d(10, [0] * 16))
    bad(d(10, [0] * 17), NV)
    bad(d(10, [0] * 10**5), NV)
    bad(d(10, []), NV)


@pytest.mark.parametrize("v", [True, 1, 1.5, None, "ab", {}, (1, 2)])
def test_noncontainers(v):
    x = d()
    x["visits"] = v
    bad(x, NV)


@pytest.mark.parametrize("s", [True, False, 1.0, "2", None, [1], b"2"])
def test_nonint(s):
    x = d()
    x["visits"][1] = s
    bad(x, "visit must be an int")
    x = d()
    x["items"] = s
    bad(x, "items must be an int")


@pytest.mark.parametrize("s", [1, 11, 0, -1, 10**30, -(10**30)])
def test_items_range(s):
    bad(d(s, [0]), "items must be 2 to 10")


@pytest.mark.parametrize("s", [-1, 5, 6, 10**30, -(10**30)])
def test_visit_range(s):
    bad(d(5, [0, s]), "visit must be 0 to items - 1")


def test_edges():
    check(d(2, [0, 1]))
    check(d(10, [9, 0]))


@pytest.mark.parametrize("x", [None, 1, "a", [], True, [("items", 1)]])
def test_data_not_dict(x):
    bad(x, KEYS)


def test_keys_exact():
    for k in ("items", "visits"):
        x = d()
        del x[k]
        bad(x, KEYS)
    x = d()
    x["extra"] = 1
    bad(x, KEYS)


def test_no_mutation_determinism_fresh_claims():
    x = d()
    y = copy.deepcopy(x)
    a, b = run(x), run(x)
    assert x == y and a == b
    a["claims"]["real_world"] = True
    a["first_visit"][0] = 99
    c = run(x)
    assert c["claims"]["real_world"] is False and c["first_visit"][0] == 0
    assert len(m.NOT_CLAIMED) == 4 and all(v is False for v in m.CLAIMS.values())


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
    base = {"items": 5, "visits": [0, 1, 1, 2, 0, 3]}
    paths = list(_int_paths(base))
    assert paths
    for p in paths:
        for cls in (_SubInt, _Quirky):
            with pytest.raises(ExplorationError) as e:
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
    base = {"items": 5, "visits": [0, 1, 1, 2, 0, 3]}
    n = 0
    for y in _variants(base):
        n += 1
        with pytest.raises(ExplorationError):
            run(y)
    assert n >= 2

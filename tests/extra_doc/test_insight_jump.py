import copy
import random

import pytest

from sugarcode.extra_doc import insight_jump as m
from sugarcode.extra_doc.insight_jump import InsightError, insight_jump as run

KEYS = "data keys must be exactly series, threshold"
NS = "series must be a list of 3 to 12 values"


def d(series=(10, 10, 12, 80, 82), threshold=50):
    return {"series": list(series), "threshold": threshold}


def bad(data, msg):
    with pytest.raises(InsightError) as e:
        run(data)
    assert str(e.value) == msg


def oracle(x):
    """Independent: scan with a running best, strictly-greater so the first wins."""
    s = x["series"]
    best, at = None, None
    changes = []
    for i in range(1, len(s)):
        c = s[i] - s[i - 1]
        changes.append(c)
        if best is None or c > best:
            best, at = c, i
    flat = 0
    for i in range(1, at):
        if s[i] == s[i - 1]:
            flat += 1
    ok = best >= x["threshold"]
    for i in range(1, len(s)):
        if i != at and (s[i] - s[i - 1]) * 2 > best:
            ok = False
    return changes, best, at, flat, ok


def check(x):
    o = run(x)
    ch, best, at, flat, ok = oracle(x)
    assert (o["changes"], o["jump"], o["jump_at"], o["plateau"], o["sudden"]) == (ch, best, at, flat, ok)
    return o


def test_hand_worked():
    o = run(d())
    assert o["changes"] == [0, 2, 68, 2] and o["jump"] == 68 and o["jump_at"] == 3
    assert o["plateau"] == 1 and o["sudden"] is True
    assert o["status"] == "completed"
    assert o["claims"] == {"measures_understanding": False, "jump_is_insight": False, "comparable_steps": False, "real_world": False}
    assert len(o["not_claimed"]) == 4
    check(d())


def test_boundaries():
    assert run(d((0, 50, 100), 50))["sudden"] is False  # other change 50 > 25
    assert run(d((0, 0, 50, 75), 50))["sudden"] is True  # other 25*2 == 50 <= 50
    assert run(d((0, 0, 50, 76), 50))["sudden"] is False  # other 26*2 > 50
    assert run(d((0, 0, 49), 49))["sudden"] is True  # jump == threshold
    assert run(d((0, 0, 49), 50))["sudden"] is False  # jump < threshold
    o = run(d((5, 9, 5, 9), 1))
    assert o["jump_at"] == 1 and o["sudden"] is False  # tie for max: first index, other change 4*2 > 4
    o = run(d((50, 40, 30), 1))
    assert o["jump"] == -10 and o["sudden"] is False
    o = run(d((7, 7, 7), 1))
    assert o["jump"] == 0 and o["plateau"] == 0 and o["jump_at"] == 1 and o["sudden"] is False


def test_random():
    rng = random.Random(890)
    for _ in range(600):
        s = [rng.randint(0, 30) for _ in range(rng.randint(3, 12))]
        check(d(s, rng.randint(1, 30)))


def test_caps():
    run(d([1] * 12))
    bad(d([1] * 13), NS)
    bad(d([1] * 10**5), NS)
    bad(d([1, 2]), NS)
    bad(d([]), NS)


@pytest.mark.parametrize("v", [True, 1, 1.5, None, "abc", {}, (1, 2, 3)])
def test_noncontainers(v):
    x = d()
    x["series"] = v
    bad(x, NS)


@pytest.mark.parametrize("s", [True, False, 1.0, "5", None, [1], b"5"])
def test_nonint(s):
    x = d()
    x["series"][2] = s
    bad(x, "series values must be ints")
    x = d()
    x["threshold"] = s
    bad(x, "threshold must be an int")


@pytest.mark.parametrize("s", [-1, 101, 10**30, -(10**30)])
def test_range(s):
    x = d()
    x["series"][0] = s
    bad(x, "series values must be 0 to 100")


@pytest.mark.parametrize("s", [0, 101, -5, 10**30])
def test_threshold_range(s):
    x = d()
    x["threshold"] = s
    bad(x, "threshold must be 1 to 100")


@pytest.mark.parametrize("s", [0, 100])
def test_edges(s):
    check(d((s, s, s), 1))


@pytest.mark.parametrize("x", [None, 1, "a", [], True, [("series", 1)]])
def test_data_not_dict(x):
    bad(x, KEYS)


def test_keys_exact():
    for k in ("series", "threshold"):
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
    a["changes"].append(99)
    c = run(x)
    assert c["claims"]["real_world"] is False and len(c["changes"]) == 4
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
    base = {"series": [10, 10, 12, 80, 82], "threshold": 50}
    paths = list(_int_paths(base))
    assert paths
    for p in paths:
        for cls in (_SubInt, _Quirky):
            with pytest.raises(InsightError) as e:
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
    base = {"series": [10, 10, 12, 80, 82], "threshold": 50}
    n = 0
    for y in _variants(base):
        n += 1
        with pytest.raises(InsightError):
            run(y)
    assert n >= 4


def test_threshold_edges():
    assert run(d((0, 0, 100), 100))["sudden"] is True
    assert run(d((0, 0, 99), 100))["sudden"] is False
    assert run(d((0, 0, 1), 1))["sudden"] is True
    check(d((3, 3, 4), 1))
    check(d((3, 3, 4), 100))

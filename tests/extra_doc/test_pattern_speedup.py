import copy
import random
from fractions import Fraction as F

import pytest

from sugarcode.extra_doc import pattern_speedup as m
from sugarcode.extra_doc.pattern_speedup import SpeedupError, pattern_speedup as run

KEYS = "data keys must be exactly trials"
NT = "trials must be a list of 2 to 12 trials"
ET = "each trial must be a list of [pattern, ms]"


def d(t=((1, 400), (0, 600), (1, 500), (0, 700))):
    return {"trials": [list(e) for e in t]}


def bad(data, msg):
    with pytest.raises(SpeedupError) as e:
        run(data)
    assert str(e.value) == msg


def oracle(x):
    """Independent: running sums and counts in one loop."""
    s = {0: 0, 1: 0}
    c = {0: 0, 1: 0}
    for p, ms in x["trials"]:
        s[p] += ms
        c[p] += 1
    pm = F(s[1], c[1]) if c[1] else None
    om = F(s[0], c[0]) if c[0] else None
    gap = (om - pm) if (pm is not None and om is not None) else None
    return c[1], c[0], pm, om, gap


def check(x):
    o = run(x)
    n1, n0, pm, om, gap = oracle(x)
    assert (o["pattern_trials"], o["other_trials"]) == (n1, n0)
    for key, val in (("pattern_mean", pm), ("other_mean", om), ("speedup", gap)):
        assert (o[key] is None) == (val is None)
        if val is not None:
            assert F(o[key]) == val
    assert o["faster_on_pattern"] is (gap is not None and gap > 0)
    return o


def test_hand_worked():
    o = run(d())
    assert o["pattern_trials"] == 2 and o["other_trials"] == 2
    assert o["pattern_mean"] == "450" and o["other_mean"] == "650" and o["speedup"] == "200"
    assert o["faster_on_pattern"] is True
    assert o["status"] == "completed"
    assert o["claims"] == {"unaware": False, "speedup_is_learning": False, "measured_properly": False, "real_world": False}
    assert len(o["not_claimed"]) == 4
    check(d())


def test_cases():
    o = run(d([(1, 500), (0, 500)]))
    assert o["speedup"] == "0" and o["faster_on_pattern"] is False
    o = run(d([(1, 700), (0, 500)]))
    assert o["speedup"] == "-200" and o["faster_on_pattern"] is False
    o = run(d([(1, 100), (1, 101)]))
    assert o["pattern_mean"] == "201/2" and o["other_mean"] is None and o["speedup"] is None and o["faster_on_pattern"] is False
    o = run(d([(0, 100), (0, 2000)]))
    assert o["pattern_mean"] is None and o["other_mean"] == "1050" and o["speedup"] is None
    o = run(d([(1, 100), (0, 101)]))
    assert o["speedup"] == "1" and o["faster_on_pattern"] is True
    o = run(d([(1, 100), (1, 101), (0, 300)]))
    assert o["speedup"] == "399/2"


def test_random():
    rng = random.Random(907)
    for _ in range(600):
        check(d([(rng.randint(0, 1), rng.randint(100, 130)) for _ in range(rng.randint(2, 12))]))


def test_caps():
    run(d([(1, 100)] * 12))
    bad(d([(1, 100)] * 13), NT)
    bad(d([(1, 100)] * 10**5), NT)
    bad(d([(1, 100)]), NT)
    bad(d([]), NT)


@pytest.mark.parametrize("v", [True, 1, 1.5, None, "ab", {}, (([1, 100]), ([0, 100]))])
def test_noncontainers(v):
    bad({"trials": v}, NT)


@pytest.mark.parametrize("s", [None, 1, "ab", [1], [1, 100, 1], [], (1, 100), {}, True])
def test_bad_trial(s):
    x = d()
    x["trials"][1] = s
    bad(x, ET)


@pytest.mark.parametrize("s", [True, False, 1.0, "2", None, [1], b"2"])
def test_nonint(s):
    for pos in (0, 1):
        x = d()
        x["trials"][1][pos] = s
        bad(x, "pattern and ms must be ints")


@pytest.mark.parametrize("s", [2, -1, 10**30])
def test_pattern_range(s):
    x = d()
    x["trials"][0][0] = s
    bad(x, "pattern must be 0 or 1")


@pytest.mark.parametrize("s", [99, 2001, 0, -1, 10**30, -(10**30)])
def test_ms_range(s):
    x = d()
    x["trials"][0][1] = s
    bad(x, "ms must be 100 to 2000")


@pytest.mark.parametrize("s", [100, 2000])
def test_ms_edges(s):
    check(d([(1, s), (0, 100 + 2000 - s)]))


@pytest.mark.parametrize("x", [None, 1, "a", [], True, [("trials", 1)]])
def test_data_not_dict(x):
    bad(x, KEYS)


def test_keys_exact():
    bad({}, KEYS)
    x = d()
    x["extra"] = 1
    bad(x, KEYS)


def test_no_mutation_determinism_fresh_claims():
    x = d()
    y = copy.deepcopy(x)
    a, b = run(x), run(x)
    assert x == y and a == b
    a["claims"]["real_world"] = True
    c = run(x)
    assert c["claims"]["real_world"] is False and c["speedup"] == "200"
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
    base = {"trials": [[1, 400], [0, 600], [1, 500], [0, 700]]}
    paths = list(_int_paths(base))
    assert paths
    for p in paths:
        for cls in (_SubInt, _Quirky):
            with pytest.raises(SpeedupError) as e:
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
    base = {"trials": [[1, 400], [0, 600], [1, 500], [0, 700]]}
    n = 0
    for y in _variants(base):
        n += 1
        with pytest.raises(SpeedupError):
            run(y)
    assert n >= 2

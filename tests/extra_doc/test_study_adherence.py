import copy
import random
from fractions import Fraction as F

import pytest

from sugarcode.extra_doc import study_adherence as m
from sugarcode.extra_doc.study_adherence import AdherenceError, study_adherence as run

KEYS = "data keys must be exactly sessions"
NS = "sessions must be a list of 1 to 10 sessions"
ES = "each session must be a list of [planned, actual]"


def d(s=((60, 60), (60, 90), (30, 10), (45, 45), (45, 50))):
    return {"sessions": [list(e) for e in s]}


def bad(data, msg):
    with pytest.raises(AdherenceError) as e:
        run(data)
    assert str(e.value) == msg


def oracle(x):
    """Independent: met flags first, then runs via string split, shortfall via max(0, .)."""
    s = x["sessions"]
    flags = "".join("1" if a >= p else "0" for p, a in s)
    longest = max(len(r) for r in flags.split("0"))
    planned = sum(e[0] for e in s)
    actual = sum(e[1] for e in s)
    short = sum(max(0, p - a) for p, a in s)
    return flags.count("1"), planned, actual, (F(actual, planned) if planned else None), short, longest


def check(x):
    o = run(x)
    met, pl, ac, ad, sh, lg = oracle(x)
    assert (o["met"], o["planned"], o["actual"], o["shortfall"], o["longest_met_run"]) == (met, pl, ac, sh, lg)
    assert (o["adherence"] is None) == (ad is None)
    if ad is not None:
        assert F(o["adherence"]) == ad
    return o


def test_hand_worked():
    o = run(d())
    assert o["met"] == 4 and o["planned"] == 240 and o["actual"] == 255 and o["adherence"] == "17/16"
    assert o["shortfall"] == 20 and o["longest_met_run"] == 2
    assert o["status"] == "completed"
    assert o["claims"] == {"real_minutes": False, "met_is_learning": False, "sensible_plans": False, "real_world": False}
    assert len(o["not_claimed"]) == 4
    check(d())


def test_cases():
    o = run(d([(0, 0)]))
    assert o["adherence"] is None and o["met"] == 1 and o["longest_met_run"] == 1 and o["shortfall"] == 0
    o = run(d([(10, 9)]))
    assert o["met"] == 0 and o["longest_met_run"] == 0 and o["shortfall"] == 1 and o["adherence"] == "9/10"
    o = run(d([(10, 10), (10, 10), (10, 9), (10, 10)]))
    assert o["longest_met_run"] == 2 and o["met"] == 3
    o = run(d([(10, 9), (10, 10), (10, 10), (10, 10)]))
    assert o["longest_met_run"] == 3
    o = run(d([(10, 10), (10, 0), (10, 10), (10, 10), (10, 10), (10, 5)]))
    assert o["longest_met_run"] == 3 and o["shortfall"] == 15
    o = run(d([(0, 240), (240, 0)]))
    assert o["shortfall"] == 240 and o["adherence"] == "1" and o["met"] == 1
    o = run(d([(0, 5)]))
    assert o["adherence"] is None and o["actual"] == 5


def test_random():
    rng = random.Random(909)
    for _ in range(600):
        check(d([(rng.randint(0, 5), rng.randint(0, 5)) for _ in range(rng.randint(1, 10))]))


def test_caps():
    run(d([(1, 1)] * 10))
    bad(d([(1, 1)] * 11), NS)
    bad(d([(1, 1)] * 10**5), NS)
    bad(d([]), NS)


@pytest.mark.parametrize("v", [True, 1, 1.5, None, "ab", {}, (([1, 1]),)])
def test_noncontainers(v):
    bad({"sessions": v}, NS)


@pytest.mark.parametrize("s", [None, 1, "ab", [1], [1, 1, 1], [], (1, 1), {}, True])
def test_bad_session(s):
    x = d()
    x["sessions"][1] = s
    bad(x, ES)


@pytest.mark.parametrize("s", [True, False, 1.0, "5", None, [1], b"5"])
def test_nonint(s):
    for pos in (0, 1):
        x = d()
        x["sessions"][2][pos] = s
        bad(x, "minutes must be ints")


@pytest.mark.parametrize("s", [-1, 241, 10**30, -(10**30)])
def test_range(s):
    for pos in (0, 1):
        x = d()
        x["sessions"][0][pos] = s
        bad(x, "minutes must be 0 to 240")


@pytest.mark.parametrize("s", [0, 240])
def test_edges(s):
    check(d([(s, s), (240 - s, s)]))


@pytest.mark.parametrize("x", [None, 1, "a", [], True, [("sessions", 1)]])
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
    assert c["claims"]["real_world"] is False and c["met"] == 4
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
    base = {"sessions": [[60, 60], [60, 90], [30, 10], [45, 45], [45, 50]]}
    paths = list(_int_paths(base))
    assert paths
    for p in paths:
        for cls in (_SubInt, _Quirky):
            with pytest.raises(AdherenceError) as e:
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
    base = {"sessions": [[60, 60], [60, 90], [30, 10], [45, 45], [45, 50]]}
    n = 0
    for y in _variants(base):
        n += 1
        with pytest.raises(AdherenceError):
            run(y)
    assert n >= 2

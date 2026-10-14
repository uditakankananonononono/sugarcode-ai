import copy
import random
from fractions import Fraction as F

import pytest

from sugarcode.extra_doc import lesson_phases as m
from sugarcode.extra_doc.lesson_phases import LessonError, lesson_phases as run

KEYS = "data keys must be exactly segments"
NS = "segments must be a list of 1 to 8 segments"
ES = "each segment must be a list of [phase, minutes]"
PH = "phase must be one of explain, model, practice, check"
ORDER = ["explain", "model", "practice", "check"]


def d(s=(("explain", 10), ("model", 5), ("practice", 20), ("check", 5), ("practice", 10))):
    return {"segments": [list(e) for e in s]}


def bad(data, msg):
    with pytest.raises(LessonError) as e:
        run(data)
    assert str(e.value) == msg


def oracle(x):
    """Independent: per-phase filter sums, order check by comparing neighbours' index in ORDER."""
    s = x["segments"]
    mins = {p: sum(m_ for q, m_ in s if q == p) for p in ORDER if any(q == p for q, _ in s)}
    total = sum(m_ for _, m_ in s)
    missing = [p for p in ORDER if not any(q == p for q, _ in s)]
    ok = True
    for a, b in zip(s, s[1:]):
        if ORDER.index(b[0]) < ORDER.index(a[0]):
            ok = False
    return mins, total, missing, ok


def check(x):
    o = run(x)
    mins, total, missing, ok = oracle(x)
    assert o["minutes"] == mins and list(o["minutes"]) == list(mins) and o["total"] == total
    assert {p: F(v) for p, v in o["shares"].items()} == {p: F(v, total) for p, v in mins.items()}
    assert list(o["shares"]) == list(mins)
    assert o["missing"] == missing and o["in_order"] == ok
    return o


def test_hand_worked():
    o = run(d())
    assert o["minutes"] == {"explain": 10, "model": 5, "practice": 30, "check": 5} and o["total"] == 50
    assert o["shares"] == {"explain": "1/5", "model": "1/10", "practice": "3/5", "check": "1/10"}
    assert o["missing"] == [] and o["in_order"] is False  # practice follows check
    assert o["status"] == "completed"
    assert o["claims"] == {"took_place": False, "right_split": False, "order_required": False, "real_world": False}
    assert len(o["not_claimed"]) == 4
    check(d())


def test_cases():
    o = run(d([("check", 4), ("explain", 4)]))
    assert o["in_order"] is False and list(o["minutes"]) == ["explain", "check"] and o["missing"] == ["model", "practice"]
    o = run(d([("practice", 7)]))
    assert o["shares"] == {"practice": "1"} and o["missing"] == ["explain", "model", "check"] and o["in_order"] is True
    o = run(d([("model", 1), ("explain", 1)]))
    assert o["in_order"] is False
    o = run(d([("explain", 1), ("explain", 2), ("model", 3)]))
    assert o["in_order"] is True and o["minutes"]["explain"] == 3
    o = run(d([("explain", 60)] * 8))
    assert o["total"] == 480 and o["shares"] == {"explain": "1"}
    o = run(d([("explain", 1), ("practice", 1), ("model", 1)]))
    assert o["in_order"] is False
    o = run(d([("explain", 1), ("model", 1), ("check", 1), ("practice", 1)]))
    assert o["in_order"] is False


def test_random():
    rng = random.Random(905)
    for _ in range(600):
        check(d([(rng.choice(ORDER), rng.randint(1, 9)) for _ in range(rng.randint(1, 8))]))


def test_caps():
    run(d([("check", 1)] * 8))
    bad(d([("check", 1)] * 9), NS)
    bad(d([("check", 1)] * 10**5), NS)
    bad(d([]), NS)


@pytest.mark.parametrize("v", [True, 1, 1.5, None, "ab", {}, ((["check", 1]),)])
def test_noncontainers(v):
    bad({"segments": v}, NS)


@pytest.mark.parametrize("s", [None, 1, "ab", ["check"], ["check", 1, 1], [], ("check", 1), {}, True])
def test_bad_segment(s):
    x = d()
    x["segments"][1] = s
    bad(x, ES)


@pytest.mark.parametrize("s", ["", "Explain", "explain ", "x", None, 1, True, b"explain", ["explain"]])
def test_bad_phase(s):
    x = d()
    x["segments"][1][0] = s
    bad(x, PH)


@pytest.mark.parametrize("s", [True, False, 1.0, "5", None, [1], b"5"])
def test_nonint_minutes(s):
    x = d()
    x["segments"][2][1] = s
    bad(x, "minutes must be an int")


@pytest.mark.parametrize("s", [0, 61, -1, 10**30, -(10**30)])
def test_minutes_range(s):
    x = d()
    x["segments"][0][1] = s
    bad(x, "minutes must be 1 to 60")


@pytest.mark.parametrize("s", [1, 60])
def test_minutes_edges(s):
    check(d([("explain", s), ("check", 61 - s)]))


@pytest.mark.parametrize("x", [None, 1, "a", [], True, [("segments", 1)]])
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
    a["minutes"]["explain"] = 99
    a["missing"].append("zz")
    c = run(x)
    assert c["claims"]["real_world"] is False and c["minutes"]["explain"] == 10 and c["missing"] == []
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
    base = {"segments": [["explain", 10], ["model", 5], ["practice", 20], ["check", 5], ["practice", 10]]}
    paths = list(_int_paths(base))
    assert paths
    for p in paths:
        for cls in (_SubInt, _Quirky):
            with pytest.raises(LessonError) as e:
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
    base = {"segments": [["explain", 10], ["model", 5], ["practice", 20], ["check", 5], ["practice", 10]]}
    n = 0
    for y in _variants(base):
        n += 1
        with pytest.raises(LessonError):
            run(y)
    assert n >= 2

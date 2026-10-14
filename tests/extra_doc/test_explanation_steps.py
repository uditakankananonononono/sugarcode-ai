import copy
import random
from fractions import Fraction as F

import pytest

from sugarcode.extra_doc import explanation_steps as m
from sugarcode.extra_doc.explanation_steps import ExplanationError, explanation_steps as run

KEYS = "data keys must be exactly steps"
NS = "steps must be a list of 1 to 10 steps"
ES = "each step must be a list of [name, examples, checked]"
NN = "name must be 1..12 characters from a-z and _"


def d(s=(("setup", 2, 1), ("apply", 0, 1), ("review", 1, 0), ("extend", 3, 1))):
    return {"steps": [list(e) for e in s]}


def bad(data, msg):
    with pytest.raises(ExplanationError) as e:
        run(data)
    assert str(e.value) == msg


def oracle(x):
    """Independent: rows sorted by key r[0]; flags by filtering rows."""
    rows = sorted(x["steps"], key=lambda r: r[0])
    total = 0
    for r in rows:
        total += r[1]
    none = [r[0] for r in rows if r[1] == 0]
    unc = [r[0] for r in rows if r[2] == 0]
    done = len([r for r in rows if r[2] == 1])
    return total, none, unc, F(done, len(rows)), (not none and not unc)


def check(x):
    o = run(x)
    total, none, unc, share, comp = oracle(x)
    assert (o["total_examples"], o["without_example"], o["unchecked"], F(o["checked_share"]), o["complete"]) == (total, none, unc, share, comp)
    return o


def test_hand_worked():
    o = run(d())
    assert o["total_examples"] == 6 and o["without_example"] == ["apply"] and o["unchecked"] == ["review"]
    assert o["checked_share"] == "3/4" and o["complete"] is False
    assert o["status"] == "completed"
    assert o["claims"] == {"clear": False, "caused_understanding": False, "sound_flags": False, "real_world": False}
    assert len(o["not_claimed"]) == 4
    check(d())


def test_cases():
    o = run(d([("a", 1, 1)]))
    assert o["complete"] is True and o["checked_share"] == "1" and o["without_example"] == [] and o["unchecked"] == []
    o = run(d([("a", 0, 1)]))
    assert o["complete"] is False and o["without_example"] == ["a"] and o["unchecked"] == []
    o = run(d([("a", 1, 0)]))
    assert o["complete"] is False and o["unchecked"] == ["a"] and o["checked_share"] == "0"
    o = run(d([("b", 0, 0), ("a", 0, 0)]))
    assert o["without_example"] == ["a", "b"] and o["unchecked"] == ["a", "b"] and o["total_examples"] == 0
    o = run(d([("a", 5, 1), ("b", 5, 1)]))
    assert o["total_examples"] == 10 and o["complete"] is True
    o = run(d([("a", 1, 1), ("b", 1, 1), ("c", 1, 0)]))
    assert o["checked_share"] == "2/3"


def test_random():
    rng = random.Random(906)
    for _ in range(500):
        names = rng.sample("abcdefghij", rng.randint(1, 10))
        check(d([(n, rng.randint(0, 2), rng.randint(0, 1)) for n in names]))


def test_caps():
    names = list("abcdefghij")
    run(d([(n, 1, 1) for n in names]))
    bad(d([(n, 1, 1) for n in names] + [("k", 1, 1)]), NS)
    bad(d([("a", 1, 1)] * 10**5), NS)
    bad(d([]), NS)


@pytest.mark.parametrize("v", [True, 1, 1.5, None, "ab", {}, ((["a", 1, 1]),)])
def test_noncontainers(v):
    bad({"steps": v}, NS)


@pytest.mark.parametrize("s", [None, 1, "ab", ["a"], ["a", 1], ["a", 1, 1, 1], [], ("a", 1, 1), {}, True])
def test_bad_step(s):
    x = d()
    x["steps"][1] = s
    bad(x, ES)


@pytest.mark.parametrize("s", ["", "A", "a1", "a-b", "a b", "a" * 13, "é", "a\n", None, 1, True, b"a", ["a"]])
def test_bad_name(s):
    bad(d([(s, 1, 1)]), NN)


@pytest.mark.parametrize("s", ["a", "z", "_", "a" * 12])
def test_good_name(s):
    check(d([(s, 1, 1)]))


@pytest.mark.parametrize("s", [True, False, 1.0, "2", None, [1], b"2"])
def test_nonint(s):
    for pos in (1, 2):
        x = d()
        x["steps"][1][pos] = s
        bad(x, "examples and checked must be ints")


@pytest.mark.parametrize("s", [-1, 6, 10**30, -(10**30)])
def test_examples_range(s):
    x = d()
    x["steps"][0][1] = s
    bad(x, "examples must be 0 to 5")


@pytest.mark.parametrize("s", [2, -1, 10**30])
def test_checked_range(s):
    x = d()
    x["steps"][0][2] = s
    bad(x, "checked must be 0 or 1")


@pytest.mark.parametrize("s", [0, 5])
def test_examples_edges(s):
    check(d([("a", s, 1)]))


def test_distinct_names():
    bad(d([("a", 1, 1), ("a", 2, 0)]), "names must be distinct")


@pytest.mark.parametrize("x", [None, 1, "a", [], True, [("steps", 1)]])
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
    a["unchecked"].append("zz")
    c = run(x)
    assert c["claims"]["real_world"] is False and c["unchecked"] == ["review"]
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
    base = {"steps": [["setup", 2, 1], ["apply", 0, 1], ["review", 1, 0], ["extend", 3, 1]]}
    paths = list(_int_paths(base))
    assert paths
    for p in paths:
        for cls in (_SubInt, _Quirky):
            with pytest.raises(ExplanationError) as e:
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
    base = {"steps": [["setup", 2, 1], ["apply", 0, 1], ["review", 1, 0], ["extend", 3, 1]]}
    n = 0
    for y in _variants(base):
        n += 1
        with pytest.raises(ExplanationError):
            run(y)
    assert n >= 2

import copy
import random
from fractions import Fraction as F

import pytest

from sugarcode.extra_doc import course_grades as m
from sugarcode.extra_doc.course_grades import GradeError, course_grades as run

KEYS = "data keys must be exactly courses"
NC = "courses must be a list of 1 to 8 courses"
EC = "each course must be a list of [name, credits, points]"
NN = "name must be 1..12 characters from a-z and _"


def d(c=(("math", 4, 3), ("art", 2, 4), ("chem", 4, 0), ("bio", 3, 2))):
    return {"courses": [list(e) for e in c]}


def bad(data, msg):
    with pytest.raises(GradeError) as e:
        run(data)
    assert str(e.value) == msg


def oracle(x):
    """Independent: sort rows by key, weighted sum in a loop, heaviest via (-credits, name)."""
    rows = sorted(x["courses"], key=lambda r: r[0])
    total = 0
    weighted = 0
    earned = 0
    for n, c, p in rows:
        total += c
        weighted += c * p
        if p:
            earned += c
    failed = [n for n, c, p in rows if p == 0]
    heavy = sorted(rows, key=lambda r: (-r[1], r[0]))[0][0]
    return total, earned, F(weighted, total), failed, heavy


def check(x):
    o = run(x)
    total, earned, avg, failed, heavy = oracle(x)
    assert (o["total_credits"], o["earned_credits"], F(o["average"]), o["failed"], o["heaviest"]) == (total, earned, avg, failed, heavy)
    return o


def test_hand_worked():
    o = run(d())
    assert o["total_credits"] == 13 and o["earned_credits"] == 9 and o["average"] == "2"
    assert o["failed"] == ["chem"] and o["heaviest"] == "chem"
    assert o["status"] == "completed"
    assert o["claims"] == {"real_grades": False, "measures_learning": False, "zero_is_fail": False, "real_world": False}
    assert len(o["not_claimed"]) == 4
    check(d())


def test_cases():
    o = run(d([("a", 3, 4)]))
    assert o["average"] == "4" and o["failed"] == [] and o["earned_credits"] == 3
    o = run(d([("a", 3, 0)]))
    assert o["average"] == "0" and o["failed"] == ["a"] and o["earned_credits"] == 0
    o = run(d([("b", 2, 1), ("a", 2, 2)]))
    assert o["heaviest"] == "a" and o["average"] == "3/2"
    o = run(d([("b", 3, 1), ("a", 2, 2)]))
    assert o["heaviest"] == "b" and o["average"] == "7/5"
    o = run(d([("a", 1, 4), ("b", 6, 1)]))
    assert o["average"] == "10/7" and o["total_credits"] == 7
    o = run(d([("z", 1, 0), ("y", 1, 0)]))
    assert o["failed"] == ["y", "z"]


def test_random():
    rng = random.Random(910)
    for _ in range(500):
        names = rng.sample("abcdefgh", rng.randint(1, 8))
        check(d([(n, rng.randint(1, 6), rng.randint(0, 4)) for n in names]))


def test_caps():
    names = list("abcdefgh")
    run(d([(n, 1, 1) for n in names]))
    bad(d([(n, 1, 1) for n in names] + [("i", 1, 1)]), NC)
    bad(d([("a", 1, 1)] * 10**5), NC)
    bad(d([]), NC)


@pytest.mark.parametrize("v", [True, 1, 1.5, None, "ab", {}, ((["a", 1, 1]),)])
def test_noncontainers(v):
    bad({"courses": v}, NC)


@pytest.mark.parametrize("s", [None, 1, "ab", ["a"], ["a", 1], ["a", 1, 1, 1], [], ("a", 1, 1), {}, True])
def test_bad_course(s):
    x = d()
    x["courses"][1] = s
    bad(x, EC)


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
        x["courses"][1][pos] = s
        bad(x, "credits and points must be ints")


@pytest.mark.parametrize("s", [0, 7, -1, 10**30, -(10**30)])
def test_credits_range(s):
    x = d()
    x["courses"][0][1] = s
    bad(x, "credits must be 1 to 6")


@pytest.mark.parametrize("s", [5, -1, 10**30, -(10**30)])
def test_points_range(s):
    x = d()
    x["courses"][0][2] = s
    bad(x, "points must be 0 to 4")


@pytest.mark.parametrize("c,p", [(1, 0), (6, 4), (1, 4), (6, 0)])
def test_edges(c, p):
    check(d([("a", c, p)]))


def test_distinct_names():
    bad(d([("a", 1, 1), ("a", 2, 0)]), "names must be distinct")


@pytest.mark.parametrize("x", [None, 1, "a", [], True, [("courses", 1)]])
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
    a["failed"].append("zz")
    c = run(x)
    assert c["claims"]["real_world"] is False and c["failed"] == ["chem"]
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
    base = {"courses": [["math", 4, 3], ["art", 2, 4], ["chem", 4, 0], ["bio", 3, 2]]}
    paths = list(_int_paths(base))
    assert paths
    for p in paths:
        for cls in (_SubInt, _Quirky):
            with pytest.raises(GradeError) as e:
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
    base = {"courses": [["math", 4, 3], ["art", 2, 4], ["chem", 4, 0], ["bio", 3, 2]]}
    n = 0
    for y in _variants(base):
        n += 1
        with pytest.raises(GradeError):
            run(y)
    assert n >= 2

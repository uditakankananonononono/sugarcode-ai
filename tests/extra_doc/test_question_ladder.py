import copy
import random
from fractions import Fraction as F

import pytest

from sugarcode.extra_doc import question_ladder as m
from sugarcode.extra_doc.question_ladder import LadderError, question_ladder as run

KEYS = "data keys must be exactly questions"
NQ = "questions must be a list of 1 to 10 questions"
EQ = "each question must be a list of [depth, answered]"


def d(q=((1, 1), (2, 1), (2, 0), (4, 1))):
    return {"questions": [list(e) for e in q]}


def bad(data, msg):
    with pytest.raises(LadderError) as e:
        run(data)
    assert str(e.value) == msg


def oracle(x):
    """Independent: depth counts via list.count, deepening by pairwise zip, deepest via sorted."""
    q = x["questions"]
    depths = [e[0] for e in q]
    by = [depths.count(k) for k in (1, 2, 3, 4)]
    ans = sorted(e[0] for e in q if e[1] == 1)
    ok = True
    for a, b in zip(depths, depths[1:]):
        if b < a:
            ok = False
    return by, F(sum(depths), len(depths)), F(len(ans), len(q)), (ans[-1] if ans else None), ok


def check(x):
    o = run(x)
    by, mean, share, deepest, ok = oracle(x)
    assert (o["by_depth"], F(o["mean_depth"]), F(o["answered_share"]), o["deepest_answered"], o["deepening"]) == (by, mean, share, deepest, ok)
    return o


def test_hand_worked():
    o = run(d())
    assert o["by_depth"] == [1, 2, 0, 1] and o["mean_depth"] == "9/4" and o["answered_share"] == "3/4"
    assert o["deepest_answered"] == 4 and o["deepening"] is True
    assert o["status"] == "completed"
    assert o["claims"] == {"labels_right": False, "deeper_is_better": False, "answers_correct": False, "real_world": False}
    assert len(o["not_claimed"]) == 4
    check(d())


def test_cases():
    o = run(d([(3, 0)]))
    assert o["deepest_answered"] is None and o["answered_share"] == "0" and o["deepening"] is True and o["by_depth"] == [0, 0, 1, 0]
    o = run(d([(3, 1), (2, 1)]))
    assert o["deepening"] is False and o["deepest_answered"] == 3
    o = run(d([(2, 1), (2, 0), (2, 1)]))
    assert o["deepening"] is True  # equal depth is not a fall
    o = run(d([(1, 1), (4, 0), (3, 1)]))
    assert o["deepening"] is False and o["deepest_answered"] == 3
    o = run(d([(4, 1), (4, 1)]))
    assert o["mean_depth"] == "4" and o["answered_share"] == "1"
    o = run(d([(1, 1), (2, 0), (1, 0)]))
    assert o["mean_depth"] == "4/3" and o["deepening"] is False


def test_random():
    rng = random.Random(902)
    for _ in range(500):
        check(d([(rng.randint(1, 4), rng.randint(0, 1)) for _ in range(rng.randint(1, 10))]))


def test_caps():
    run(d([(1, 1)] * 10))
    bad(d([(1, 1)] * 11), NQ)
    bad(d([(1, 1)] * 10**5), NQ)
    bad(d([]), NQ)


@pytest.mark.parametrize("v", [True, 1, 1.5, None, "ab", {}, (([1, 1]),)])
def test_noncontainers(v):
    bad({"questions": v}, NQ)


@pytest.mark.parametrize("s", [None, 1, "ab", [1], [1, 1, 1], [], (1, 1), {}, True])
def test_bad_question(s):
    x = d()
    x["questions"][1] = s
    bad(x, EQ)


@pytest.mark.parametrize("s", [True, False, 1.0, "2", None, [1], b"2"])
def test_nonint(s):
    for pos in (0, 1):
        x = d()
        x["questions"][1][pos] = s
        bad(x, "depth and answered must be ints")


@pytest.mark.parametrize("s", [0, 5, -1, 10**30, -(10**30)])
def test_depth_range(s):
    x = d()
    x["questions"][0][0] = s
    bad(x, "depth must be 1 to 4")


@pytest.mark.parametrize("s", [2, -1, 10**30])
def test_answered_range(s):
    x = d()
    x["questions"][0][1] = s
    bad(x, "answered must be 0 or 1")


@pytest.mark.parametrize("s", [1, 4])
def test_depth_edges(s):
    check(d([(s, 1)]))


@pytest.mark.parametrize("x", [None, 1, "a", [], True, [("questions", 1)]])
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
    a["by_depth"][0] = 99
    c = run(x)
    assert c["claims"]["real_world"] is False and c["by_depth"] == [1, 2, 0, 1]
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
    base = {"questions": [[1, 1], [2, 1], [2, 0], [4, 1]]}
    paths = list(_int_paths(base))
    assert paths
    for p in paths:
        for cls in (_SubInt, _Quirky):
            with pytest.raises(LadderError) as e:
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
    base = {"questions": [[1, 1], [2, 1], [2, 0], [4, 1]]}
    n = 0
    for y in _variants(base):
        n += 1
        with pytest.raises(LadderError):
            run(y)
    assert n >= 2

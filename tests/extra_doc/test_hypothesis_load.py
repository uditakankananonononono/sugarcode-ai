import copy
import random
from fractions import Fraction as F

import pytest

from sugarcode.extra_doc import hypothesis_load as m
from sugarcode.extra_doc.hypothesis_load import ProblemError, hypothesis_load as run

KEYS = "data keys must be exactly problems"
NP = "problems must be a list of 1 to 8 problems"
EP = "each problem must be a list of [name, hypotheses, resolved]"
NN = "name must be 1..12 characters from a-z and _"


def d(p=(("leak", 3, 1), ("noise", 5, 0), ("heat", 2, 1))):
    return {"problems": [list(e) for e in p]}


def bad(data, msg):
    with pytest.raises(ProblemError) as e:
        run(data)
    assert str(e.value) == msg


def oracle(x):
    """Independent: rows sorted by name as a list, heaviest via sort on (-h, name)."""
    rows = sorted(x["problems"], key=lambda r: r[0])
    hyp = {r[0]: r[1] for r in rows}
    res = [r[0] for r in rows if r[2] == 1]
    unres = [r[0] for r in rows if r[2] == 0]
    total = 0
    for r in rows:
        total += r[1]
    mean = None
    if res:
        mean = F(sum(hyp[n] for n in res), len(res))
    heavy = sorted(rows, key=lambda r: (-r[1], r[0]))[0][0]
    return hyp, res, unres, total, mean, heavy


def check(x):
    o = run(x)
    hyp, res, unres, total, mean, heavy = oracle(x)
    assert (o["hypotheses"], o["resolved"], o["unresolved"], o["total"], o["heaviest"]) == (hyp, res, unres, total, heavy)
    assert list(o["hypotheses"]) == sorted(hyp)
    assert (o["mean_per_resolved"] is None) == (mean is None)
    if mean is not None:
        assert F(o["mean_per_resolved"]) == mean
    return o


def test_hand_worked():
    o = run(d())
    assert o["hypotheses"] == {"heat": 2, "leak": 3, "noise": 5} and list(o["hypotheses"]) == ["heat", "leak", "noise"]
    assert o["resolved"] == ["heat", "leak"] and o["unresolved"] == ["noise"] and o["total"] == 10
    assert o["mean_per_resolved"] == "5/2" and o["heaviest"] == "noise"
    assert o["status"] == "completed"
    assert o["claims"] == {"worked": False, "more_is_better": False, "sound_judgement": False, "real_world": False}
    assert len(o["not_claimed"]) == 4
    check(d())


def test_cases():
    o = run(d([("a", 4, 0)]))
    assert o["mean_per_resolved"] is None and o["resolved"] == [] and o["unresolved"] == ["a"] and o["heaviest"] == "a"
    o = run(d([("b", 4, 1), ("a", 4, 1)]))
    assert o["heaviest"] == "a" and o["mean_per_resolved"] == "4"
    o = run(d([("b", 4, 1), ("a", 3, 1)]))
    assert o["heaviest"] == "b" and o["mean_per_resolved"] == "7/2"
    o = run(d([("a", 1, 1), ("b", 2, 1), ("c", 2, 1)]))
    assert o["mean_per_resolved"] == "5/3" and o["heaviest"] == "b"
    o = run(d([("a", 10, 1), ("b", 1, 0)]))
    assert o["total"] == 11 and o["mean_per_resolved"] == "10"


def test_random():
    rng = random.Random(901)
    for _ in range(500):
        names = rng.sample("abcdefgh", rng.randint(1, 8))
        check(d([(n, rng.randint(1, 4), rng.randint(0, 1)) for n in names]))


def test_caps():
    names = list("abcdefgh")
    run(d([(n, 1, 1) for n in names]))
    bad(d([(n, 1, 1) for n in names] + [("i", 1, 1)]), NP)
    bad(d([("a", 1, 1)] * 10**5), NP)
    bad(d([]), NP)


@pytest.mark.parametrize("v", [True, 1, 1.5, None, "ab", {}, ((["a", 1, 1]),)])
def test_noncontainers(v):
    bad({"problems": v}, NP)


@pytest.mark.parametrize("s", [None, 1, "ab", ["a"], ["a", 1], ["a", 1, 1, 1], [], ("a", 1, 1), {}, True])
def test_bad_problem(s):
    x = d()
    x["problems"][1] = s
    bad(x, EP)


@pytest.mark.parametrize("s", ["", "A", "a1", "a-b", "a b", "a" * 13, "é", "a\n", None, 1, True, b"a", ["a"]])
def test_bad_name(s):
    bad(d([(s, 1, 1)]), NN)


@pytest.mark.parametrize("s", ["a", "z", "_", "a" * 12])
def test_good_name(s):
    check(d([(s, 1, 1)]))


@pytest.mark.parametrize("s", [True, False, 1.0, "5", None, [1], b"5"])
def test_nonint(s):
    for pos in (1, 2):
        x = d()
        x["problems"][1][pos] = s
        bad(x, "hypotheses and resolved must be ints")


@pytest.mark.parametrize("s", [0, 11, -1, 10**30, -(10**30)])
def test_hypotheses_range(s):
    x = d()
    x["problems"][0][1] = s
    bad(x, "hypotheses must be 1 to 10")


@pytest.mark.parametrize("s", [2, -1, 10**30])
def test_resolved_range(s):
    x = d()
    x["problems"][0][2] = s
    bad(x, "resolved must be 0 or 1")


@pytest.mark.parametrize("s", [1, 10])
def test_hypotheses_edges(s):
    check(d([("a", s, 1), ("b", 11 - s, 0)]))


def test_distinct_names():
    bad(d([("a", 1, 1), ("a", 2, 0)]), "names must be distinct")


@pytest.mark.parametrize("x", [None, 1, "a", [], True, [("problems", 1)]])
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
    a["hypotheses"]["leak"] = 99
    a["resolved"].append("zz")
    c = run(x)
    assert c["claims"]["real_world"] is False and c["hypotheses"]["leak"] == 3 and c["resolved"] == ["heat", "leak"]
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
    base = {"problems": [["leak", 3, 1], ["noise", 5, 0], ["heat", 2, 1]]}
    paths = list(_int_paths(base))
    assert paths
    for p in paths:
        for cls in (_SubInt, _Quirky):
            with pytest.raises(ProblemError) as e:
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
    base = {"problems": [["leak", 3, 1], ["noise", 5, 0], ["heat", 2, 1]]}
    n = 0
    for y in _variants(base):
        n += 1
        with pytest.raises(ProblemError):
            run(y)
    assert n >= 4

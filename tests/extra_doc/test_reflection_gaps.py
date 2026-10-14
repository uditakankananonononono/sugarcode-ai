import copy
import random
from fractions import Fraction as F

import pytest

from sugarcode.extra_doc import reflection_gaps as m
from sugarcode.extra_doc.reflection_gaps import ReflectionError, reflection_gaps as run

KEYS = "data keys must be exactly entries"
NE = "entries must be a list of 1 to 12 entries"
EE = "each entry must be a list of [day, words]"


def d(ent=((0, 100), (7, 50), (14, 150))):
    return {"entries": [list(e) for e in ent]}


def bad(data, msg):
    with pytest.raises(ReflectionError) as e:
        run(data)
    assert str(e.value) == msg


def oracle(x):
    """Independent: pairwise zip of days, regularity by set size."""
    ent = x["entries"]
    days = [e[0] for e in ent]
    gaps = [b - a for a, b in zip(days, days[1:])]
    total = 0
    for _, w in ent:
        total += w
    reg = len(gaps) >= 2 and len(set(gaps)) == 1
    return len(ent), total, F(total, len(ent)), gaps, (sorted(gaps)[-1] if gaps else None), reg


def check(x):
    o = run(x)
    n, total, mean, gaps, longest, reg = oracle(x)
    assert (o["count"], o["total_words"], F(o["mean_words"]), o["gaps"], o["longest_gap"], o["regular"]) == (n, total, mean, gaps, longest, reg)
    return o


def test_hand_worked():
    o = run(d())
    assert o["count"] == 3 and o["total_words"] == 300 and o["mean_words"] == "100"
    assert o["gaps"] == [7, 7] and o["longest_gap"] == 7 and o["regular"] is True
    assert o["status"] == "completed"
    assert o["claims"] == {"entries_exist": False, "words_are_depth": False, "spacing_is_habit": False, "real_world": False}
    assert len(o["not_claimed"]) == 4
    check(d())


def test_cases():
    o = run(d([(5, 7)]))
    assert o["gaps"] == [] and o["longest_gap"] is None and o["regular"] is False and o["mean_words"] == "7"
    o = run(d([(1, 0), (3, 1)]))
    assert o["gaps"] == [2] and o["regular"] is False and o["mean_words"] == "1/2"
    o = run(d([(0, 1), (2, 1), (5, 1)]))
    assert o["gaps"] == [2, 3] and o["longest_gap"] == 3 and o["regular"] is False
    o = run(d([(0, 1), (3, 1), (5, 1)]))
    assert o["longest_gap"] == 3 and o["gaps"] == [3, 2]
    o = run(d([(0, 500), (365, 500)]))
    assert o["longest_gap"] == 365 and o["total_words"] == 1000
    o = run(d([(0, 1), (1, 2), (2, 2), (3, 2)]))
    assert o["regular"] is True and o["mean_words"] == "7/4"


def test_random():
    rng = random.Random(898)
    for _ in range(500):
        days = sorted(rng.sample(range(0, 40), rng.randint(1, 12)))
        check(d([(x, rng.randint(0, 9)) for x in days]))


def test_caps():
    run(d([(i, 1) for i in range(12)]))
    bad(d([(i, 1) for i in range(13)]), NE)
    bad(d([(1, 1)] * 10**5), NE)
    bad(d([]), NE)


@pytest.mark.parametrize("v", [True, 1, 1.5, None, "ab", {}, (([1, 2]),)])
def test_noncontainers(v):
    bad({"entries": v}, NE)


@pytest.mark.parametrize("s", [None, 1, "ab", [1], [1, 2, 3], [], (1, 2), {}, True])
def test_bad_entry(s):
    x = d()
    x["entries"][1] = s
    bad(x, EE)


@pytest.mark.parametrize("s", [True, False, 1.0, "5", None, [1], b"5"])
def test_nonint(s):
    for pos in (0, 1):
        x = d()
        x["entries"][1][pos] = s
        bad(x, "day and words must be ints")


@pytest.mark.parametrize("s", [-1, 366, 10**30, -(10**30)])
def test_day_range(s):
    x = d()
    x["entries"][0][0] = s
    bad(x, "day must be 0 to 365")


@pytest.mark.parametrize("s", [-1, 501, 10**30, -(10**30)])
def test_words_range(s):
    x = d()
    x["entries"][2][1] = s
    bad(x, "words must be 0 to 500")


def test_edges():
    check(d([(0, 0), (365, 500)]))
    check(d([(365, 500)]))


def test_increasing():
    bad(d([(5, 1), (5, 1)]), "days must be strictly increasing")
    bad(d([(5, 1), (4, 1)]), "days must be strictly increasing")
    run(d([(5, 1), (6, 1)]))


@pytest.mark.parametrize("x", [None, 1, "a", [], True, [("entries", 1)]])
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
    a["gaps"].append(99)
    c = run(x)
    assert c["claims"]["real_world"] is False and c["gaps"] == [7, 7]
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
    base = {"entries": [[0, 100], [7, 50], [14, 150]]}
    paths = list(_int_paths(base))
    assert paths
    for p in paths:
        for cls in (_SubInt, _Quirky):
            with pytest.raises(ReflectionError) as e:
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
    base = {"entries": [[0, 100], [7, 50], [14, 150]]}
    n = 0
    for y in _variants(base):
        n += 1
        with pytest.raises(ReflectionError):
            run(y)
    assert n >= 2


def test_order_checked_against_previous_not_first():
    bad(d([(5, 1), (10, 1), (7, 1)]), "days must be strictly increasing")
    bad(d([(5, 1), (10, 1), (12, 1), (11, 1)]), "days must be strictly increasing")


def test_regular_compares_every_gap_to_the_first():
    assert run(d([(0, 1), (3, 1), (5, 1), (7, 1)]))["regular"] is False  # gaps 3,2,2
    assert run(d([(0, 1), (2, 1), (5, 1), (8, 1)]))["regular"] is False  # gaps 2,3,3
    assert run(d([(0, 1), (2, 1), (4, 1), (6, 1)]))["regular"] is True
    assert run(d([(0, 1), (2, 1), (4, 1), (7, 1)]))["regular"] is False  # gaps 2,2,3

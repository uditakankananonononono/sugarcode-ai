import copy
import itertools
import random

import pytest

from sugarcode.extra_doc import fault_vote as m
from sugarcode.extra_doc.fault_vote import VoteError, fault_vote as run

KEYS = "data keys must be exactly f, results"
NR = "results must be a list of 3 to 9 entries"


def d(results=(7, 7, 9), f=1):
    return {"results": list(results), "f": f}


def bad(data, msg):
    with pytest.raises(VoteError) as e:
        run(data)
    assert str(e.value) == msg


def oracle(r, f):
    """Independent: count each answer by scanning the list, collect candidates by position."""
    cands = []
    for v in r:
        if v is None:
            continue
        c = sum(1 for w in r if w is not None and w == v)
        if c >= f + 1 and v not in cands:
            cands.append(v)
    dec = cands[0] if len(cands) == 1 else None
    seen = sorted({v for v in r if v is not None})
    votes = [[v, sum(1 for w in r if w is not None and w == v)] for v in seen]
    diss = [v for v in r if v is not None and v != dec]
    crashed = sum(1 for v in r if v is None)
    return dec, votes, crashed, diss, dec is not None and (crashed + len(diss) > 0)


def check(x):
    o = run(x)
    dec, votes, crashed, diss, masked = oracle(x["results"], x["f"])
    assert (o["decision"], o["votes"], o["crashed"], o["dissenters"], o["masked"]) == (dec, votes, crashed, diss, masked)
    return o


def test_hand_worked():
    o = run(d())
    assert o["decision"] == 7 and o["votes"] == [[7, 2], [9, 1]] and o["crashed"] == 0
    assert o["dissenters"] == [9] and o["masked"] is True and o["status"] == "completed"
    assert o["claims"] == {"fault_tolerant_system": False, "real_faults_covered": False, "independent": False, "real_world": False}
    assert len(o["not_claimed"]) == 4
    check(d())


def test_unanimous_is_not_masked():
    o = run(d((5, 5, 5), 1))
    assert o["decision"] == 5 and o["masked"] is False and o["dissenters"] == [] and o["crashed"] == 0


def test_crash_counts_and_masks():
    o = run(d((5, None, 5), 1))
    assert o["decision"] == 5 and o["crashed"] == 1 and o["masked"] is True and o["votes"] == [[5, 2]]
    assert o["dissenters"] == []
    o = run(d((None, None, 5), 1))
    assert o["decision"] is None and o["crashed"] == 2 and o["masked"] is False and o["dissenters"] == [5]


def test_threshold_is_f_plus_one():
    assert run(d((1, 1, 2, 3, 4), 2))["decision"] is None  # 2 votes < 3
    assert run(d((1, 1, 1, 3, 4), 2))["decision"] == 1  # 3 votes
    assert run(d((1, 2, 3), 0))["decision"] is None  # f=0: three answers each at 1 vote -> ambiguous
    assert run(d((1, 1, 1), 0))["decision"] == 1
    assert run(d((1, 2, 2), 0))["decision"] is None  # two answers reach f+1 = 1


def test_two_winners_is_no_decision():
    o = run(d((1, 1, 2, 2), 1))
    assert o["decision"] is None and o["votes"] == [[1, 2], [2, 2]] and o["dissenters"] == [1, 1, 2, 2]
    assert o["masked"] is False


def test_negative_zero_and_order():
    o = run(d((-3, 0, -3, 0, -3), 2))
    assert o["decision"] == -3 and o["votes"] == [[-3, 3], [0, 2]] and o["dissenters"] == [0, 0]
    o = run(d((9, 0, 0, 9, None, 1000, -1000, 0, 0), 3))
    assert o["decision"] == 0 and o["votes"] == [[-1000, 1], [0, 4], [9, 2], [1000, 1]]
    assert o["dissenters"] == [9, 9, 1000, -1000] and o["crashed"] == 1


def test_zero_is_an_answer_not_none():
    o = run(d((0, 0, None), 1))
    assert o["decision"] == 0 and o["votes"] == [[0, 2]]


def test_exhaustive_small():
    for r in itertools.product([None, 0, 1, 2], repeat=4):
        for f in (0, 1):
            check(d(r, f))


def test_random():
    rng = random.Random(521)
    for _ in range(1500):
        n = rng.randint(3, 9)
        f = rng.randint(0, (n - 1) // 2)
        r = [rng.choice([None, rng.randint(-1000, 1000), 5, 5, 6]) for _ in range(n)]
        check(d(r, f))


def test_caps():
    run(d([1] * 9, 4))
    bad(d([1] * 10), NR)
    bad(d([1] * 10**5), NR)
    bad(d([1, 1]), NR)
    bad(d([]), NR)


@pytest.mark.parametrize("v", [True, 1, "abc", None, (1, 1, 1), {}])
def test_noncontainers(v):
    x = d()
    x["results"] = v
    bad(x, NR)


@pytest.mark.parametrize("s", [True, False, 1.0, "5", [1], b"5", 0.0])
def test_nonint(s):
    x = d()
    x["results"][1] = s
    bad(x, "result must be an int or None")
    x = d()
    x["f"] = s
    bad(x, "f must be an int")
    x = d()
    x["f"] = None
    bad(x, "f must be an int")


@pytest.mark.parametrize("s", [-1001, 1001, 10**30, -(10**30)])
def test_result_range(s):
    x = d()
    x["results"][0] = s
    bad(x, "result must be -1000 to 1000")


def test_edges():
    check(d((-1000, 1000, 1000), 1))
    check(d((1000,) * 3, 1))


@pytest.mark.parametrize("s", [-1, 5, 10**30])
def test_f_range(s):
    bad(d(f=s), "f must be 0 to 4")


def test_redundancy_floor():
    bad(d((1, 1, 1), 2), "results must hold at least 2*f+1 entries")
    bad(d((1,) * 8, 4), "results must hold at least 2*f+1 entries")
    run(d((1,) * 9, 4))
    run(d((1,) * 5, 2))
    run(d((1,) * 3, 1))


def test_tuple_refused():
    x = d()
    x["results"] = (7, 7, 9)
    bad(x, NR)


@pytest.mark.parametrize("x", [None, 1, "a", [], True, [("f", 1)]])
def test_data_not_dict(x):
    bad(x, KEYS)


def test_keys_exact():
    for k in list(d()):
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
    a["votes"][0][1] = 99
    c = run(x)
    assert c["claims"]["real_world"] is False and c["votes"][0][1] == 2
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
    base = {"results": [7, 7, 9], "f": 1}
    paths = list(_int_paths(base))
    assert paths
    for p in paths:
        for cls in (_SubInt, _Quirky):
            with pytest.raises(VoteError) as e:
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
    base = {"results": [7, 7, 9], "f": 1}
    n = 0
    for y in _variants(base):
        n += 1
        with pytest.raises(VoteError):
            run(y)
    assert n >= 2

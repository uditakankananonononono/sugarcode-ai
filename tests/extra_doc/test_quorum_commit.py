import copy
import random

import pytest

from sugarcode.extra_doc import quorum_commit as m
from sugarcode.extra_doc.quorum_commit import QuorumError, quorum_commit as run

KEYS = "data keys must be exactly acks, nodes"
NA = "acks must be a list of 1 to 10 entries"
NE = "each entry must be a list of at most nodes node ids"


def d(acks=None, nodes=5):
    if acks is None:
        acks = [[0, 1, 2], [0, 1, 2, 3], [0, 1], [0, 1, 2, 3, 4]]
    return {"nodes": nodes, "acks": copy.deepcopy(acks)}


def bad(data, msg):
    with pytest.raises(QuorumError) as e:
        run(data)
    assert str(e.value) == msg


def oracle(nodes, acks):
    """Independent: majority by doubling (2 * count > nodes); commit stops at the first short entry."""
    ok = [2 * len(set(r)) > nodes for r in acks]
    commit = ok.index(False) if False in ok else len(ok)
    held = sum(ok[commit:])
    return (nodes // 2 + 1), [len(r) for r in acks], commit, held


def check(x):
    o = run(x)
    q, c, ci, h = oracle(x["nodes"], x["acks"])
    assert (o["quorum"], o["counts"], o["commit_index"], o["held_back"]) == (q, c, ci, h)
    return o


def test_hand_worked():
    # 5 nodes, quorum 3 ; counts 3,4,2,5 ; entry 2 is short so commit stops at 2 and entry 3 is held back
    o = run(d())
    assert o["quorum"] == 3 and o["counts"] == [3, 4, 2, 5]
    assert o["commit_index"] == 2 and o["held_back"] == 1
    assert o["status"] == "completed"
    assert o["claims"] == {"consensus": False, "agree_on_state": False, "safe_under_failure": False, "real_world": False}
    assert len(o["not_claimed"]) == 4
    check(d())


def test_quorum_sizes():
    for n, q in ((3, 2), (4, 3), (5, 3), (6, 4), (7, 4)):
        o = run(d([[]], n))
        assert o["quorum"] == q and o["commit_index"] == 0
        o = run(d([list(range(q))], n))
        assert o["commit_index"] == 1
        o = run(d([list(range(q - 1))], n))
        assert o["commit_index"] == 0


def test_all_commit_and_none_commit():
    o = run(d([[0, 1], [1, 2], [0, 2]], 3))
    assert o["commit_index"] == 3 and o["held_back"] == 0
    o = run(d([[0], [], [0]], 3))
    assert o["commit_index"] == 0 and o["held_back"] == 0
    o = run(d([[0], [0, 1], [0, 1]], 3))
    assert o["commit_index"] == 0 and o["held_back"] == 2


def test_held_back_counts_only_replicated():
    o = run(d([[0, 1], [0], [0, 1], [2], [0, 1, 2]], 3))
    assert o["commit_index"] == 1 and o["held_back"] == 2


def test_even_cluster_half_is_not_a_majority():
    o = run(d([[0, 1]], 4))
    assert o["commit_index"] == 0
    o = run(d([[0, 1, 2]], 4))
    assert o["commit_index"] == 1


def test_random():
    rng = random.Random(585)
    for _ in range(1500):
        n = rng.randint(3, 7)
        acks = [rng.sample(range(n), rng.randint(0, n)) for _ in range(rng.randint(1, 10))]
        check(d(acks, n))


def test_caps():
    run(d([[0]] * 10, 3))
    bad(d([[0]] * 11, 3), NA)
    bad(d([[0]] * 10**5, 3), NA)
    bad(d([], 3), NA)


@pytest.mark.parametrize("v", [True, 1, "ab", None, ((0,),), {}])
def test_noncontainers(v):
    x = d()
    x["acks"] = v
    bad(x, NA)


@pytest.mark.parametrize("v", [True, 1, "ab", None, (0, 1), {}])
def test_bad_rows(v):
    x = d()
    x["acks"][1] = v
    bad(x, NE)


def test_row_too_long_and_tuple_rows():
    bad(d([[0, 1, 2, 0]], 3), NE)
    bad(d([[0, 1, 2, 3]], 3), NE)
    bad(d([[0] * 10**5], 3), NE)
    bad(d([(0, 1)], 3), NE)
    x = d()
    x["acks"] = tuple(x["acks"])
    bad(x, NA)


@pytest.mark.parametrize("s", [True, False, 1.0, "1", None, [1], b"1"])
def test_nonint(s):
    x = d()
    x["acks"][1][1] = s
    bad(x, "node id must be an int")
    x = d()
    x["nodes"] = s
    bad(x, "nodes must be an int")


@pytest.mark.parametrize("s", [-1, 5, 10**30, -(10**30)])
def test_id_range(s):
    x = d()
    x["acks"][0][0] = s
    bad(x, "node id must be 0 to nodes-1")


def test_duplicates():
    bad(d([[1, 1]], 3), "node ids in an entry must be different")
    bad(d([[0, 1, 0]], 3), "node ids in an entry must be different")
    run(d([[0, 1, 2]], 3))


@pytest.mark.parametrize("s", [2, 8, 0, -1, 10**30])
def test_nodes_range(s):
    bad(d(nodes=s), "nodes must be 3 to 7")


def test_edges():
    check(d([[0, 1, 2, 3, 4, 5, 6]] * 10, 7))
    check(d([[]], 3))


@pytest.mark.parametrize("x", [None, 1, "a", [], True, [("acks", 1)]])
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
    a["counts"][0] = 99
    c = run(x)
    assert c["claims"]["real_world"] is False and c["counts"][0] == 3
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
    base = {"nodes": 5, "acks": [[0, 1, 2], [0, 1, 2, 3], [0, 1], [0, 1, 2, 3, 4]]}
    paths = list(_int_paths(base))
    assert paths
    for p in paths:
        for cls in (_SubInt, _Quirky):
            with pytest.raises(QuorumError) as e:
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
    base = {"nodes": 5, "acks": [[0, 1, 2], [0, 1, 2, 3], [0, 1], [0, 1, 2, 3, 4]]}
    n = 0
    for y in _variants(base):
        n += 1
        with pytest.raises(QuorumError):
            run(y)
    assert n >= 2

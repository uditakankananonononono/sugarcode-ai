import copy
import itertools
import random

import pytest

from sugarcode.extra_doc import causal_model as m
from sugarcode.extra_doc.causal_model import ModelError, causal_model as run

KEYS = "data keys must be exactly concepts, links"
CS = "concepts must be a list of 1..12 names"
LS = "links must be a list of at most 40 [cause, effect] pairs"
CN = "concept must be 1..12 characters from a-z and _"


def d(cs=("rain", "wet", "slip", "sun"), ls=(("rain", "wet"), ("wet", "slip"))):
    return {"concepts": list(cs), "links": [list(x) for x in ls]}


def bad(data, msg):
    with pytest.raises(ModelError) as e:
        run(data)
    assert str(e.value) == msg


def closure(cs, ls):
    """Independent: Warshall transitive closure over a boolean matrix."""
    idx = {c: i for i, c in enumerate(cs)}
    n = len(cs)
    r = [[False] * n for _ in range(n)]
    for a, b in ls:
        r[idx[a]][idx[b]] = True
    for k, i, j in itertools.product(range(n), repeat=3):
        if r[i][k] and r[k][j]:
            r[i][j] = True
    return idx, r


def valid_orders_ok(order, ls):
    pos = {c: i for i, c in enumerate(order)}
    return all(pos[a] < pos[b] for a, b in ls)


def check(data):
    o = run(data)
    cs = sorted(data["concepts"])
    ls = [tuple(x) for x in data["links"]]
    idx, r = closure(cs, ls)
    for c in cs:
        assert o["model"][c]["downstream"] == [e for e in cs if r[idx[c]][idx[e]]]
        assert o["model"][c]["effects"] == sorted(b for a, b in ls if a == c)
        assert o["model"][c]["causes"] == sorted(a for a, b in ls if b == c)
    cyc = any(r[i][i] for i in range(len(cs)))
    assert o["has_cycle"] == cyc
    assert o["roots"] == [c for c in cs if not any(b == c for _, b in ls)]
    assert o["leaves"] == [c for c in cs if not any(a == c for a, _ in ls)]
    if cyc:
        assert o["order"] is None
    else:
        assert sorted(o["order"]) == cs and valid_orders_ok(o["order"], ls)
        # lexicographically smallest topological order, by brute force over permutations for small n
        if len(cs) <= 6:
            best = min(p for p in itertools.permutations(cs) if valid_orders_ok(p, ls))
            assert o["order"] == list(best)
    return o


def test_hand_worked():
    o = run(d())
    assert o["model"]["rain"] == {"effects": ["wet"], "causes": [], "downstream": ["slip", "wet"]}
    assert o["model"]["slip"] == {"effects": [], "causes": ["wet"], "downstream": []}
    assert o["roots"] == ["rain", "sun"] and o["leaves"] == ["slip", "sun"]
    assert o["has_cycle"] is False and o["order"] == ["rain", "sun", "wet", "slip"]
    assert o["status"] == "completed"
    assert o["claims"] == {"links_true": False, "complete": False, "unique_order": False, "real_world": False}
    assert len(o["not_claimed"]) == 4


def test_cycle_and_edges():
    o = check(d(("a", "b", "c"), (("a", "b"), ("b", "c"), ("c", "a"))))
    assert o["has_cycle"] is True and o["order"] is None
    assert o["model"]["a"]["downstream"] == ["a", "b", "c"]
    o = check(d(("a", "b", "c"), (("a", "b"), ("b", "a"))))      # cycle plus an isolated node
    assert o["has_cycle"] is True
    o = check(d(("a",), ()))
    assert o["order"] == ["a"] and o["roots"] == ["a"] and o["leaves"] == ["a"]
    o = check(d(("b", "a"), (("b", "a"),)))
    assert o["order"] == ["b", "a"]
    o = check(d(("a", "b", "c", "d"), (("d", "a"), ("c", "a"))))
    assert o["order"] == ["b", "c", "d", "a"]


def test_random():
    rng = random.Random(880)
    names = ["a", "b", "c", "d", "e", "f"]
    for _ in range(500):
        n = rng.randint(1, 6)
        cs = names[:n]
        pairs = [(x, y) for x in cs for y in cs if x != y]
        ls = rng.sample(pairs, rng.randint(0, min(len(pairs), 8)))
        if rng.random() < 0.6:
            ls = [(x, y) for x, y in ls if x < y]
        rng.shuffle(cs)
        check(d(cs, ls))


def test_caps():
    cs = [chr(97 + i) for i in range(12)]
    run(d(cs, ()))
    bad(d(cs + ["m"], ()), CS)
    bad(d([], ()), CS)
    pairs = [(x, y) for x in cs for y in cs if x != y][:40]
    run(d(cs, pairs))
    assert len(pairs) == 40
    bad(d(cs, pairs + [pairs[0]]), LS)
    x = d(cs, pairs)
    x["links"] = x["links"] + [["a", "b"]] * 10**5
    bad(x, LS)
    bad(d(("a", "a")), "concepts must be distinct")


@pytest.mark.parametrize("s", ["", "A", "a1", "a-b", "a b", "a" * 13, "é", "a\n", None, 1, True, ["a"]])
def test_bad_concept(s):
    bad(d((s,), ()), CN)


@pytest.mark.parametrize("s", ["a", "z", "_", "a" * 12])
def test_good_concept(s):
    check(d((s,), ()))


@pytest.mark.parametrize("v", [True, False, 1, 1.5, None, "ab", {}, ("a",)])
def test_noncontainers(v):
    x = d()
    x["concepts"] = v
    bad(x, CS)
    x = d()
    x["links"] = v
    bad(x, LS)
    x["links"] = [v]
    bad(x, "link must be a [cause, effect] pair")
    for p in (["a"], ["a", "b", "c"]):
        x["links"] = [p]
        bad(x, "link must be a [cause, effect] pair")


def test_link_checks():
    bad(d(("a", "b"), (("a", "z"),)), "link must use known concepts")
    bad(d(("a", "b"), (("z", "a"),)), "link must use known concepts")
    bad(d(("a", "b"), ((1, "a"),)), "link must use known concepts")
    bad(d(("a", "b"), (("a", None),)), "link must use known concepts")
    bad(d(("a", "b"), ((["a"], "b"),)), "link must use known concepts")
    bad(d(("a", "b"), (("a", ["b"]),)), "link must use known concepts")
    bad(d(("a", "b"), (({}, "b"),)), "link must use known concepts")
    bad(d(("a", "b"), (("a", "a"),)), "link must join two different concepts")
    bad(d(("a", "b"), (("a", "b"), ("a", "b"))), "links must be distinct")
    run(d(("a", "b"), (("a", "b"), ("b", "a"))))


@pytest.mark.parametrize("x", [None, 1, "a", [], True, [("concepts", 1)]])
def test_data_not_dict(x):
    bad(x, KEYS)


def test_keys_exact():
    for k in ("concepts", "links"):
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
    a["roots"].append("zz")
    a["model"]["rain"]["effects"].append("zz")
    r = run(x)
    assert r["claims"]["real_world"] is False and r["roots"] == ["rain", "sun"] and r["model"]["rain"]["effects"] == ["wet"]
    assert m.CLAIMS["real_world"] is False


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
    base = d()
    n = 0
    for y in _variants(base):
        n += 1
        with pytest.raises(ModelError):
            run(y)
    assert n >= 4

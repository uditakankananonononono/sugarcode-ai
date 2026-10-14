import copy
import random
from fractions import Fraction as F

import pytest

from sugarcode.extra_doc import association_pairs as m
from sugarcode.extra_doc.association_pairs import AssociationError, association_pairs as run

KEYS = "data keys must be exactly pairs"
NP = "pairs must be a list of 1 to 12 presentations"
EP = "each presentation must be a list of two stimuli"
SN = "stimulus must be 1..12 characters from a-z and _"


def d(pairs=(("bell", "food"), ("food", "bell"), ("bell", "light"))):
    return {"pairs": [list(p) for p in pairs]}


def bad(data, msg):
    with pytest.raises(AssociationError) as e:
        run(data)
    assert str(e.value) == msg


def oracle(x):
    """Independent: scan every possible name pair with counting, no dict tally."""
    pr = x["pairs"]
    names = sorted({s for p in pr for s in p})
    rows = []
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            c = len([p for p in pr if sorted(p) == [a, b]])
            if c:
                rows.append([a, b, c])
    top = max(r[2] for r in rows)
    first = [r for r in rows if r[2] == top][0]
    partners = {}
    for n in names:
        partners[n] = len([r for r in rows if n in r[:2]])
    return rows, first, F(top, len(pr)), partners


def check(x):
    o = run(x)
    rows, first, share, partners = oracle(x)
    assert (o["counts"], o["strongest"], F(o["strongest_share"]), o["partners"]) == (rows, first, share, partners)
    assert list(o["partners"]) == sorted(o["partners"])
    return o


def test_hand_worked():
    o = run(d())
    assert o["counts"] == [["bell", "food", 2], ["bell", "light", 1]]
    assert o["strongest"] == ["bell", "food", 2] and o["strongest_share"] == "2/3"
    assert o["partners"] == {"bell": 2, "food": 1, "light": 1}
    assert o["status"] == "completed"
    assert o["claims"] == {"happened": False, "association_learned": False, "order_irrelevant": False, "real_world": False}
    assert len(o["not_claimed"]) == 4
    check(d())


def test_ties_and_order():
    o = run(d([("b", "a"), ("c", "d")]))
    assert o["strongest"] == ["a", "b", 1] and o["strongest_share"] == "1/2"
    o = run(d([("c", "d"), ("a", "b"), ("b", "a"), ("d", "c")]))
    assert o["strongest"] == ["a", "b", 2] and o["counts"] == [["a", "b", 2], ["c", "d", 2]]
    o = run(d([("z", "a")]))
    assert o["counts"] == [["a", "z", 1]] and o["strongest_share"] == "1"
    o = run(d([("a", "b"), ("a", "c"), ("a", "c")]))
    assert o["strongest"] == ["a", "c", 2] and o["partners"] == {"a": 2, "b": 1, "c": 1}


def test_random():
    rng = random.Random(891)
    for _ in range(500):
        pr = [rng.sample("abcd", 2) for _ in range(rng.randint(1, 12))]
        check(d(pr))


def test_caps():
    run(d([("a", "b")] * 12))
    bad(d([("a", "b")] * 13), NP)
    bad(d([("a", "b")] * 10**5), NP)
    bad(d([]), NP)


@pytest.mark.parametrize("v", [True, 1, 1.5, None, "ab", {}, (("a", "b"),)])
def test_noncontainers(v):
    bad({"pairs": v}, NP)


@pytest.mark.parametrize("s", [None, 1, "ab", ["a"], ["a", "b", "c"], [], ("a", "b"), {}, True])
def test_bad_presentation(s):
    x = d()
    x["pairs"][1] = s
    bad(x, EP)


@pytest.mark.parametrize("s", ["", "A", "a1", "a-b", "a b", "a" * 13, "é", "a\n", None, 1, True, b"a", ["a"]])
def test_bad_stimulus(s):
    bad(d([("a", s)]), SN)
    bad(d([(s, "a")]), SN)


@pytest.mark.parametrize("s", ["a", "z", "_", "a" * 12])
def test_good_stimulus(s):
    check(d([(s, "q")]))


def test_same_stimulus():
    bad(d([("a", "a")]), "a presentation needs two different stimuli")
    bad(d([("a", "b"), ("c", "c")]), "a presentation needs two different stimuli")


@pytest.mark.parametrize("x", [None, 1, "a", [], True, [("pairs", 1)]])
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
    a["counts"][0][2] = 99
    a["partners"]["bell"] = 99
    c = run(x)
    assert c["claims"]["real_world"] is False and c["counts"][0][2] == 2 and c["partners"]["bell"] == 2
    assert len(m.NOT_CLAIMED) == 4 and all(v is False for v in m.CLAIMS.values())


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
    base = {"pairs": [["bell", "food"], ["food", "bell"], ["bell", "light"]]}
    n = 0
    for y in _variants(base):
        n += 1
        with pytest.raises(AssociationError):
            run(y)
    assert n >= 4

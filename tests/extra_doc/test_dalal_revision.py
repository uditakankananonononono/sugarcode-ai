import copy
import itertools
import random

import pytest

from sugarcode.extra_doc import dalal_revision as m
from sugarcode.extra_doc.dalal_revision import RevisionError, dalal_revision as run

KEYS = "data keys must be exactly atoms, base, info"


def d(atoms=("a", "b"), base=(("a",), ("b",)), info=(("!a",),)):
    return {"atoms": list(atoms), "base": [list(c) for c in base], "info": [list(c) for c in info]}


def bad(data, msg):
    with pytest.raises(RevisionError) as e:
        run(data)
    assert str(e.value) == msg


def holds(clauses, world):
    for c in clauses:
        ok = False
        for lit in c:
            ok = ok or (not world[lit[1:]] if lit[0] == "!" else world[lit])
        if not ok:
            return False
    return True


def oracle(x):
    """Independent: worlds as dicts of bools, distances by set symmetric difference of true atoms."""
    at = sorted(x["atoms"])
    worlds = [dict(zip(at, bits)) for bits in itertools.product([False, True], repeat=len(at))]
    B = [w for w in worlds if holds(x["base"], w)]
    I = [w for w in worlds if holds(x["info"], w)]
    tr = lambda w: {k for k, v in w.items() if v}
    if not B or not I:
        return B, I, I, 0
    dist = lambda w: min(len(tr(w) ^ tr(b)) for b in B)
    best = min(dist(w) for w in I)
    return B, I, [w for w in I if dist(w) == best], best


def check(x):
    o = run(x)
    B, I, R, best = oracle(x)
    at = sorted(x["atoms"])
    enc = lambda w: "".join("1" if w[a] else "0" for a in at)
    assert (o["base_models"], o["info_models"], o["distance"]) == (len(B), len(I), best)
    assert o["revised"] == [enc(w) for w in R]
    ent = [a for a in at if all(w[a] for w in R)] + []
    exp = []
    for a in at:
        if all(w[a] for w in R):
            exp.append(a)
        elif all(not w[a] for w in R):
            exp.append("!" + a)
    assert o["entailed"] == exp
    return o


def test_hand_worked():
    o = run(d())
    # base models: only 11. info: a false -> 00, 01. distances to 11: 2 and 1 -> revised {01}
    assert (o["base_models"], o["info_models"]) == (1, 2) and o["revised"] == ["01"] and o["distance"] == 1
    assert o["entailed"] == ["!a", "b"]
    assert o["status"] == "completed"
    assert o["claims"] == {"real_beliefs": False, "right_operator": False, "revised_true": False, "real_world": False}
    assert len(o["not_claimed"]) == 4
    check(d())


def test_cases():
    o = check(d(base=(("a",), ("!a",)), info=(("b",),)))        # inconsistent base: info models only
    assert o["base_models"] == 0 and o["distance"] == 0 and o["revised"] == ["01", "11"] and o["entailed"] == ["b"]
    o = check(d(info=(("a",),)))                                # info already consistent with base: distance 0
    assert o["distance"] == 0 and o["revised"] == ["11"]
    o = check(d(base=(("a", "b"),), info=(("!a",), ("!b",))))   # base 01,10,11; info 00 -> distance 1 from 01 and 10
    assert o["revised"] == ["00"] and o["distance"] == 1
    o = check(d(base=(("a",),), info=(("!a", "!b"),)))          # info 00,01,10; base 10,11 -> 10 at distance 0
    assert o["revised"] == ["10"] and o["distance"] == 0
    o = check(d(("b", "a"), (("a",),), (("!a",),)))             # atoms given unsorted: output order is alphabetical
    assert o["revised"] == ["00", "01"] and o["distance"] == 1
    bad(d(info=(("a",), ("!a",))), "new information is inconsistent")


def test_random():
    rng = random.Random(882)
    names = ["a", "b", "c", "d", "e"]
    for _ in range(400):
        n = rng.randint(1, 5)
        at = names[:n]
        rng.shuffle(at)

        def cls():
            return [[("!" if rng.random() < 0.5 else "") + rng.choice(at) for _ in range(rng.randint(1, 3))] for _ in range(rng.randint(1, 4))]
        x = {"atoms": at, "base": cls(), "info": cls()}
        if not oracle(x)[1]:
            bad(x, "new information is inconsistent")
        else:
            check(x)


def test_validation():
    run(d(("a",), (("a",),), (("a",),)))
    run(d(tuple("abcde"), (("a",),) * 8, (("b",),) * 8))
    bad(d(tuple("abcdef")), "atoms must be a list of 1..5 names")
    bad(d(()), "atoms must be a list of 1..5 names")
    bad(d(("a", "a")), "atoms must be distinct")
    bad(d(base=()), "base must be a list of 1..8 clauses")
    bad(d(base=(("a",),) * 9), "base must be a list of 1..8 clauses")
    bad(d(info=()), "info must be a list of 1..8 clauses")
    bad(d(info=(("a",),) * 9), "info must be a list of 1..8 clauses")
    bad(d(base=((),)), "each clause in base must be a list of 1..4 literals")
    bad(d(base=(("a",) * 5,)), "each clause in base must be a list of 1..4 literals")
    run(d(base=(("a",) * 4,)))
    bad(d(info=((),)), "each clause in info must be a list of 1..4 literals")
    bad(d(info=(("a",) * 5,)), "each clause in info must be a list of 1..4 literals")
    bad(d(base=(("z",),)), "literal must use a known atom")
    bad(d(info=(("!z",),)), "literal must use a known atom")
    bad(d(base=(("!",),)), "literal must use a known atom")
    bad(d(base=(("!!a",),)), "literal must use a known atom")
    bad(d(base=(("A",),)), "literal must use a known atom")
    bad(d(base=((1,),)), "literal must be a string")
    bad(d(info=((None,),)), "literal must be a string")


@pytest.mark.parametrize("s", ["", "A", "a1", "a-b", "a b", "a" * 13, "é", "a\n", None, 1, True, ["a"], "!a"])
def test_bad_atom(s):
    bad(d((s,), (("a",),), (("a",),)), "atom must be 1..12 characters from a-z and _")


@pytest.mark.parametrize("s", ["a", "z", "_", "a" * 12])
def test_good_atom(s):
    run(d((s,), ((s,),), ((s,),)))


@pytest.mark.parametrize("v", [True, False, 1, 1.5, None, "ab", {}, ("a",)])
def test_noncontainers(v):
    for k, msg in (("atoms", "atoms must be a list of 1..5 names"), ("base", "base must be a list of 1..8 clauses"),
                   ("info", "info must be a list of 1..8 clauses")):
        x = d()
        x[k] = v
        bad(x, msg)
    x = d()
    x["base"] = [v]
    bad(x, "each clause in base must be a list of 1..4 literals")
    x = d()
    x["info"] = [v]
    bad(x, "each clause in info must be a list of 1..4 literals")


@pytest.mark.parametrize("x", [None, 1, "a", [], True, [("atoms", 1)]])
def test_data_not_dict(x):
    bad(x, KEYS)


def test_keys_exact():
    for k in ("atoms", "base", "info"):
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
    a["revised"].append("zz")
    a["entailed"].append("zz")
    r = run(x)
    assert r["claims"]["real_world"] is False and r["revised"] == ["01"] and r["entailed"] == ["!a", "b"]
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
        with pytest.raises(RevisionError):
            run(y)
    assert n >= 4

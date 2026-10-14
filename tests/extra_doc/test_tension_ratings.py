import copy
import random
from fractions import Fraction as F

import pytest

from sugarcode.extra_doc import tension_ratings as m
from sugarcode.extra_doc.tension_ratings import TensionError, tension_ratings as run

KEYS = "data keys must be exactly regions"
RG = "regions must be a list of 1..10 regions"
RK = "region keys must be exactly after, before, name"
NM = "name must be 1..12 characters from a-z and _"


def r(n, b, a):
    return {"name": n, "before": b, "after": a}


def d(*rs):
    return {"regions": list(rs)}


def bad(data, msg):
    with pytest.raises(TensionError) as e:
        run(data)
    assert str(e.value) == msg


def check(data):
    """Independent: recompute with max() over an indexed key (-change, index) to pin the tie rule."""
    o = run(data)
    rs = data["regions"]
    ch = [x["before"] - x["after"] for x in rs]
    assert [(x["name"], x["change"]) for x in o["regions"]] == [(x["name"], c) for x, c in zip(rs, ch)]
    assert o["total_change"] == sum(ch) and o["total_before"] == sum(x["before"] for x in rs)
    tb = o["total_before"]
    assert o["share_reduced"] == (None if tb == 0 else str(F(sum(ch), tb)))
    assert (o["improved"], o["equal"], o["worsened"]) == (sum(c > 0 for c in ch), sum(c == 0 for c in ch), sum(c < 0 for c in ch))
    i = min(range(len(ch)), key=lambda k: (-ch[k], k))
    assert o["largest_change"] == rs[i]["name"]
    return o


def test_hand_worked():
    o = run(d(r("neck", 8, 5), r("jaw", 6, 6), r("back", 7, 8)))
    assert [x["change"] for x in o["regions"]] == [3, 0, -1]
    assert (o["total_change"], o["total_before"], o["share_reduced"]) == (2, 21, "2/21")
    assert (o["improved"], o["equal"], o["worsened"], o["largest_change"]) == (1, 1, 1, "neck")
    assert o["status"] == "completed"
    assert o["claims"] == {"accurate_ratings": False, "causal": False, "lasting": False, "health_claim": False}
    assert len(o["not_claimed"]) == 4


def test_ties_zero_and_negative():
    assert check(d(r("a", 5, 3), r("b", 5, 3)))["largest_change"] == "a"
    assert check(d(r("b", 5, 3), r("a", 5, 3)))["largest_change"] == "b"
    assert check(d(r("a", 5, 4), r("b", 5, 3)))["largest_change"] == "b"
    o = check(d(r("a", 0, 0)))
    assert o["share_reduced"] is None and o["largest_change"] == "a"
    o = check(d(r("a", 1, 4), r("b", 2, 9)))
    assert o["largest_change"] == "a" and o["total_change"] == -10 and o["worsened"] == 2
    assert check(d(r("a", 10, 0)))["share_reduced"] == "1"


def test_random():
    rng = random.Random(808)
    names = ["a", "b", "c", "dd", "e_", "f", "g", "h", "i", "j"]
    for _ in range(500):
        k = rng.randint(1, 10)
        check(d(*[r(names[i], rng.randint(0, 10), rng.randint(0, 10)) for i in range(k)]))


def test_caps():
    names = list("abcdefghij")
    run(d(*[r(n, 1, 1) for n in names]))
    bad(d(*[r(n, 1, 1) for n in names], r("k", 1, 1)), RG)
    bad({"regions": [r("a", 1, 1)] * 10**5}, RG)
    bad(d(), RG)
    bad(d(r("a", 1, 1), r("a", 2, 2)), "region names must be unique")
    bad(d(r("a", 11, 0)), "before out of range")
    bad(d(r("a", -1, 0)), "before out of range")
    bad(d(r("a", 0, 11)), "after out of range")
    bad(d(r("a", 0, -1)), "after out of range")
    run(d(r("a", 0, 10)))
    run(d(r("a", 10, 0)))


@pytest.mark.parametrize("v", [True, False, 1.0, 1.5, None, "1", [1], {}])
def test_nonint(v):
    bad(d(r("a", v, 1)), "before must be an int")
    bad(d(r("a", 1, v)), "after must be an int")


@pytest.mark.parametrize("s", ["", "A", "a1", "a-b", "a b", "a" * 13, "é", "a\n", None, 1, True, ["a"]])
def test_bad_name(s):
    bad(d(r(s, 1, 1)), NM)


@pytest.mark.parametrize("s", ["a", "z", "_", "a" * 12])
def test_good_name(s):
    check(d(r(s, 1, 2)))


@pytest.mark.parametrize("v", [True, False, 1, 1.5, None, "ab", {}, ("a",)])
def test_noncontainer(v):
    bad({"regions": v}, RG)
    bad({"regions": [v]}, RK)


def test_region_keys_exact():
    bad(d({"name": "a", "before": 1}), RK)
    bad(d({"name": "a", "after": 1}), RK)
    bad(d({"before": 1, "after": 1}), RK)
    bad(d({"name": "a", "before": 1, "after": 1, "x": 1}), RK)


@pytest.mark.parametrize("x", [None, 1, "a", [], True, [("regions", 1)]])
def test_data_not_dict(x):
    bad(x, KEYS)


def test_keys_exact():
    bad({}, KEYS)
    bad({"regions": [r("a", 1, 1)], "x": 1}, KEYS)


def test_no_mutation_determinism_fresh_claims():
    x = d(r("a", 5, 3), r("b", 1, 1))
    y = copy.deepcopy(x)
    a, b = run(x), run(x)
    assert x == y and a == b
    a["claims"]["health_claim"] = True
    a["regions"][0]["change"] = 99
    q = run(x)
    assert q["claims"]["health_claim"] is False and q["regions"][0]["change"] == 2 and m.CLAIMS["health_claim"] is False


class SubInt(int):
    pass


class Quirky(int):
    """int subclass whose arithmetic lies: a witness for the rows[0:] mutant."""
    def __sub__(self, other):
        return self


def test_int_subclasses_refused_in_every_slot():
    for v in (SubInt(1), Quirky(1)):
        bad(d(r("a", v, 1)), "before must be an int")
        bad(d(r("a", 1, v)), "after must be an int")
        bad(d(r("a", 1, 1), r("b", v, 0)), "before must be an int")
        bad(d(r("a", 1, 1), r("b", 0, v)), "after must be an int")


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
    base = d(r("a", 5, 3), r("b", 1, 1))
    n = 0
    for y in _variants(base):
        n += 1
        with pytest.raises(TensionError):
            run(y)
    assert n >= 4

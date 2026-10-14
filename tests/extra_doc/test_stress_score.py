import copy
import random
from fractions import Fraction as F

import pytest

from sugarcode.extra_doc import stress_score as m
from sugarcode.extra_doc.stress_score import StressError, stress_score as run

KEYS = "data keys must be exactly high_from, items, low_below"
IT = "items must be a list of 1..30 [weight, rating] pairs"


def d(items=((2, 4), (3, 1), (5, 0)), lo=20, hi=60):
    return {"items": [list(i) for i in items], "low_below": lo, "high_from": hi}


def bad(data, msg):
    with pytest.raises(StressError) as e:
        run(data)
    assert str(e.value) == msg


def check(x):
    """Independent: expand each item into `weight` unit votes; band by integer cross-multiplication."""
    o = run(x)
    votes = [r for w, r in x["items"] for _ in range(w)]
    score, top = sum(votes), 4 * len(votes)
    assert (o["score"], o["maximum"]) == (score, top) and F(o["share"]) == F(score, top)
    band = "low" if score * 100 < x["low_below"] * top else "high" if score * 100 >= x["high_from"] * top else "medium"
    assert o["band"] == band
    return o


def test_hand_worked():
    o = run(d())
    # score 2*4 + 3*1 + 0 = 11 ; max 4*10 = 40 ; share 11/40 = 27.5%
    assert (o["score"], o["maximum"], o["share"], o["band"]) == (11, 40, "11/40", "medium")
    assert run(d(lo=28))["band"] == "low"
    assert run(d(lo=27))["band"] == "medium"
    assert run(d(hi=27))["band"] == "high" and run(d(lo=1, hi=28))["band"] == "medium"
    assert o["status"] == "completed"
    assert o["claims"] == {"accurate_ratings": False, "clinical": False, "cut_points_valid": False, "health_claim": False}
    assert len(o["not_claimed"]) == 4


def test_exact_boundaries():
    # share exactly 50%: 2 items weight 1 ratings 4 and 0 -> 4/8
    x = d([(1, 4), (1, 0)], 50, 51)
    assert check(x)["band"] == "medium"          # not below 50
    assert check(d([(1, 4), (1, 0)], 51, 52))["band"] == "low"
    assert check(d([(1, 4), (1, 0)], 49, 50))["band"] == "high"     # at high_from counts as high
    assert check(d([(1, 4), (1, 0)], 48, 49))["band"] == "high"
    assert check(d([(1, 0)], 1, 2))["band"] == "low"
    assert check(d([(1, 4)], 1, 100))["band"] == "high"
    assert check(d([(10, 4)], 99, 100))["band"] == "high"


def test_random():
    rng = random.Random(804)
    for _ in range(500):
        lo = rng.randint(1, 99)
        check(d([(rng.randint(1, 10), rng.randint(0, 4)) for _ in range(rng.randint(1, 8))], lo, rng.randint(lo + 1, 100)))


def test_caps():
    run(d([(10, 4)] * 30))
    bad(d([(1, 1)] * 31), IT)
    bad(d([(1, 1)] * 10**5), IT)
    bad(d([]), IT)
    bad(d([(0, 1)]), "weight out of range")
    bad(d([(11, 1)]), "weight out of range")
    bad(d([(1, -1)]), "rating out of range")
    bad(d([(1, 5)]), "rating out of range")
    bad(d(lo=0), "low_below out of range")
    bad(d(lo=101), "low_below out of range")
    bad(d(hi=0), "high_from out of range")
    bad(d(hi=101), "high_from out of range")
    bad(d(lo=30, hi=30), "low_below must be below high_from")
    bad(d(lo=31, hi=30), "low_below must be below high_from")
    run(d(lo=99, hi=100))
    run(d(lo=1, hi=2))


@pytest.mark.parametrize("v", [True, False, 1.0, 1.5, None, "1", [1], {}])
def test_nonint(v):
    bad(d([(v, 1)]), "weight must be an int")
    bad(d([(1, v)]), "rating must be an int")
    bad(d(lo=v), "low_below must be an int")
    bad(d(hi=v), "high_from must be an int")


@pytest.mark.parametrize("v", [True, False, 1, 1.5, None, "ab", {}, ("a",)])
def test_noncontainer(v):
    x = d()
    x["items"] = v
    bad(x, IT)
    x["items"] = [v]
    bad(x, "item must be a [weight, rating] pair")
    for p in ([1], [1, 2, 3]):
        x["items"] = [p]
        bad(x, "item must be a [weight, rating] pair")


@pytest.mark.parametrize("x", [None, 1, "a", [], True, [("items", 1)]])
def test_data_not_dict(x):
    bad(x, KEYS)


def test_keys_exact():
    for k in ("items", "low_below", "high_from"):
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
    a["claims"]["health_claim"] = True
    a["not_claimed"].append("x")
    r = run(x)
    assert r["claims"]["health_claim"] is False and len(r["not_claimed"]) == 4 and m.CLAIMS["health_claim"] is False


def test_pins_scale_and_cutpoint_bounds():
    x = d([(10, 4)] * 4 + [(7, 4), (3, 3)], 99, 100)        # share 197/200 = 98.5%
    assert check(x)["share"] == "197/200" and run(x)["band"] == "low"
    bad(d(lo=100, hi=100), "low_below must be below high_from")
    bad(d(lo=1, hi=1), "low_below must be below high_from")
    bad(d(lo=100, hi=101), "high_from out of range")


def test_pin_high_scale():
    x = d([(10, 4)] * 4 + [(9, 4), (1, 3)], 1, 100)         # share 199/200 = 99.5%
    assert check(x)["share"] == "199/200" and run(x)["band"] == "medium"


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
    base = d()
    paths = list(_int_paths(base))
    assert paths
    for p in paths:
        for cls in (_SubInt, _Quirky):
            with pytest.raises(StressError) as e:
                run(_put(base, p, cls(_get(base, p))))
            assert "must be an int" in str(e.value) or "must be ints" in str(e.value)


def _get(x, path):
    for k in path:
        x = x[k]
    return x

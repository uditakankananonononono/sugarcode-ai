import copy
import random

import pytest

from sugarcode.extra_doc import session_streaks as m
from sugarcode.extra_doc.session_streaks import StreakError, session_streaks as run

KEYS = "data keys must be exactly days"
LEN = "days must be a list of 1..365 ints"


def bad(data, msg):
    with pytest.raises(StreakError) as e:
        run(data)
    assert str(e.value) == msg


def check(days):
    """Independent: walk every calendar day between first and last using a set of logged days."""
    o = run({"days": days})
    logged = set(days)
    best = cur = 0
    gap = bestgap = 0
    nstreaks = 0
    for day in range(days[0], days[-1] + 1):
        if day in logged:
            if cur == 0:
                nstreaks += 1
            cur += 1
            best = max(best, cur)
            bestgap = max(bestgap, gap)
            gap = 0
        else:
            cur = 0
            gap += 1
    assert (o["sessions"], o["streaks"], o["longest_streak"], o["current_streak"], o["longest_gap"], o["span"]) == \
        (len(days), nstreaks, best, cur, bestgap, days[-1] - days[0] + 1)
    return o


def test_hand_worked():
    o = run({"days": [3, 4, 5, 9, 10, 20]})
    assert (o["sessions"], o["streaks"], o["longest_streak"], o["current_streak"], o["longest_gap"], o["span"]) == (6, 3, 3, 1, 9, 18)
    assert o["status"] == "completed"
    assert o["claims"] == {"accurate_days": False, "benefit": False, "predictive": False, "health_claim": False}
    assert len(o["not_claimed"]) == 4
    check([3, 4, 5, 9, 10, 20])


def test_edges():
    o = check([7])
    assert (o["streaks"], o["longest_streak"], o["current_streak"], o["longest_gap"], o["span"]) == (1, 1, 1, 0, 1)
    assert check([0, 1, 2, 3])["current_streak"] == 4
    assert check([0, 2])["longest_gap"] == 1
    assert check([0, 5, 6, 7, 8])["current_streak"] == 4 and check([0, 5, 6, 7, 8])["longest_streak"] == 4
    assert check([1, 2, 3, 10, 11])["longest_streak"] == 3 and check([1, 2, 3, 10, 11])["current_streak"] == 2
    assert check([0, 3, 4, 10])["longest_gap"] == 5
    assert check([0, 10, 12])["longest_gap"] == 9


def test_random():
    rng = random.Random(807)
    for _ in range(500):
        days = sorted(rng.sample(range(0, 60), rng.randint(1, 30)))
        check(days)
    check(list(range(365)))
    check(list(range(0, 100000, 274))[:365])


def test_caps():
    run({"days": list(range(365))})
    run({"days": [0, 100000]})
    bad({"days": list(range(366))}, LEN)
    bad({"days": list(range(10**5))}, LEN)
    bad({"days": []}, LEN)
    bad({"days": [100001]}, "day out of range")
    bad({"days": [-1]}, "day out of range")
    bad({"days": [1, 1]}, "days must be strictly increasing")
    bad({"days": [2, 1]}, "days must be strictly increasing")
    run({"days": [0]})


@pytest.mark.parametrize("v", [True, False, 1.0, 1.5, None, "1", [1], {}])
def test_nonint(v):
    bad({"days": [v]}, "days must be ints")
    bad({"days": [0, v]}, "days must be ints")


@pytest.mark.parametrize("v", [True, False, 1, 1.5, None, "ab", {}, ("a",)])
def test_noncontainer(v):
    bad({"days": v}, LEN)


@pytest.mark.parametrize("x", [None, 1, "a", [], True, [("days", 1)]])
def test_data_not_dict(x):
    bad(x, KEYS)


def test_keys_exact():
    bad({}, KEYS)
    bad({"days": [1], "x": 1}, KEYS)


def test_no_mutation_determinism_fresh_claims():
    x = {"days": [1, 2, 5]}
    y = copy.deepcopy(x)
    a, b = run(x), run(x)
    assert x == y and a == b
    a["claims"]["health_claim"] = True
    a["not_claimed"].append("x")
    r = run(x)
    assert r["claims"]["health_claim"] is False and len(r["not_claimed"]) == 4 and m.CLAIMS["health_claim"] is False


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
    base = {"days": [1, 2, 5]}
    paths = list(_int_paths(base))
    assert paths
    for p in paths:
        for cls in (_SubInt, _Quirky):
            with pytest.raises(StreakError) as e:
                run(_put(base, p, cls(_get(base, p))))
            assert "must be an int" in str(e.value) or "must be ints" in str(e.value)


def _get(x, path):
    for k in path:
        x = x[k]
    return x

import copy
import itertools
import random
from fractions import Fraction as F

import pytest

from sugarcode.extra_doc import self_control_log as m
from sugarcode.extra_doc.self_control_log import LogError, self_control_log as run

KEYS = "data keys must be exactly events"


def bad(data, msg):
    with pytest.raises(LogError) as e:
        run(data)
    assert str(e.value) == msg


def oracle(ev):
    """Independent: itertools.groupby runs."""
    runs = [(k, len(list(g))) for k, g in itertools.groupby(ev)]
    lr = max([n for k, n in runs if k == 1], default=0)
    lg = max([n for k, n in runs if k == 0], default=0)
    fin = runs[-1][1] if runs[-1][0] == 1 else 0
    return lr, lg, fin


def check(ev):
    o = run({"events": ev})
    lr, lg, fin = oracle(ev)
    assert (o["count"], o["resisted"], o["gave_in"]) == (len(ev), sum(ev), ev.count(0))
    assert F(o["resist_rate"]) == F(sum(ev), len(ev))
    assert (o["longest_resisted_run"], o["longest_gave_in_run"], o["final_resisted_run"]) == (lr, lg, fin)
    return o


def test_hand_worked():
    o = run({"events": [1, 1, 0, 0, 0, 1, 1, 1, 1, 0, 1, 1]})
    assert (o["count"], o["resisted"], o["gave_in"], o["resist_rate"]) == (12, 8, 4, "2/3")
    assert (o["longest_resisted_run"], o["longest_gave_in_run"], o["final_resisted_run"]) == (4, 3, 2)
    assert o["status"] == "completed"
    assert o["claims"] == {"accurate_log": False, "measures_self_control": False, "predictive": False, "health_claim": False}
    assert len(o["not_claimed"]) == 4


def test_edges():
    o = check([1])
    assert o["resist_rate"] == "1" and o["final_resisted_run"] == 1 and o["longest_gave_in_run"] == 0
    o = check([0])
    assert o["resist_rate"] == "0" and o["final_resisted_run"] == 0 and o["longest_resisted_run"] == 0
    assert check([1, 0])["final_resisted_run"] == 0
    assert check([0, 1])["final_resisted_run"] == 1
    assert check([0, 0, 1, 1, 1])["longest_gave_in_run"] == 2
    assert check([1, 1, 1, 0, 0])["longest_resisted_run"] == 3
    assert check([1, 0, 1, 0, 1])["longest_resisted_run"] == 1


def test_random():
    rng = random.Random(800)
    for _ in range(400):
        check([rng.randint(0, 1) for _ in range(rng.randint(1, 30))])
    check([1] * 500)
    check([0] * 500)


def test_caps():
    run({"events": [1] * 500})
    bad({"events": [1] * 501}, "events must be a list of 1..500 ints")
    bad({"events": [1] * 10**6}, "events must be a list of 1..500 ints")
    bad({"events": []}, "events must be a list of 1..500 ints")
    bad({"events": [2]}, "events must be 0 or 1")
    bad({"events": [-1]}, "events must be 0 or 1")


@pytest.mark.parametrize("v", [True, False, 1.0, 0.0, None, "1", [1], {}])
def test_nonint(v):
    bad({"events": [v]}, "events must be ints")
    bad({"events": [1, 0, v]}, "events must be ints")


@pytest.mark.parametrize("v", [True, False, 1, 1.5, None, "ab", {}, ("a",)])
def test_noncontainer(v):
    bad({"events": v}, "events must be a list of 1..500 ints")


@pytest.mark.parametrize("x", [None, 1, "a", [], True, [("events", 1)]])
def test_data_not_dict(x):
    bad(x, KEYS)


def test_keys_exact():
    bad({}, KEYS)
    bad({"events": [1], "x": 1}, KEYS)


def test_no_mutation_determinism_fresh_claims():
    x = {"events": [1, 0, 1]}
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
    base = {"events": [1, 0, 1]}
    paths = list(_int_paths(base))
    assert paths
    for p in paths:
        for cls in (_SubInt, _Quirky):
            with pytest.raises(LogError) as e:
                run(_put(base, p, cls(_get(base, p))))
            assert "must be an int" in str(e.value) or "must be ints" in str(e.value)


def _get(x, path):
    for k in path:
        x = x[k]
    return x

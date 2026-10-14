import copy
import random
from fractions import Fraction as F

import pytest

from sugarcode.extra_doc import urge_cooldown as m
from sugarcode.extra_doc.urge_cooldown import CooldownError, urge_cooldown as run

KEYS = "data keys must be exactly cooldown, events"
EV = "events must be a list of 1..200 [urge, action] pairs"


def d(ev=((0, 30), (10, 15), (50, 50)), cd=20):
    return {"events": [list(e) for e in ev], "cooldown": cd}


def bad(data, msg):
    with pytest.raises(CooldownError) as e:
        run(data)
    assert str(e.value) == msg


def check(x):
    """Independent oracle: a followed event is one whose action lies in [urge+cooldown, infinity)."""
    o = run(x)
    cd = x["cooldown"]
    ok = [e[1] in range(e[0] + cd, 10**7) for e in x["events"]]
    assert [r["followed"] for r in o["events"]] == ok
    assert [r["wait"] for r in o["events"]] == [e[1] - e[0] for e in x["events"]]
    assert o["followed"] == ok.count(True) and F(o["followed_share"]) == F(ok.count(True), len(ok))
    w = sorted(e[1] - e[0] for e in x["events"])
    assert (o["shortest_wait"], o["longest_wait"]) == (w[0], w[-1])
    return o


def test_hand_worked():
    o = run(d())
    assert o["events"] == [{"wait": 30, "followed": True}, {"wait": 5, "followed": False}, {"wait": 0, "followed": False}]
    assert (o["followed"], o["followed_share"], o["shortest_wait"], o["longest_wait"]) == (1, "1/3", 0, 30)
    assert o["status"] == "completed"
    assert o["claims"] == {"accurate_times": False, "waiting_helps": False, "shows_control": False, "health_claim": False}
    assert len(o["not_claimed"]) == 4


def test_cooldown_boundary():
    assert check(d([(0, 19)], 20))["followed"] == 0
    assert check(d([(0, 20)], 20))["followed"] == 1
    assert check(d([(0, 21)], 20))["followed"] == 1
    assert check(d([(5, 5)], 1))["followed"] == 0
    assert check(d([(0, 1)], 1))["followed"] == 1


def test_random():
    rng = random.Random(802)
    for _ in range(400):
        ev = []
        for _ in range(rng.randint(1, 10)):
            u = rng.randint(0, 100)
            ev.append((u, u + rng.randint(0, 60)))
        check(d(ev, rng.randint(1, 60)))


def test_caps():
    run(d([(1000000, 1000000)] * 200, 100000))
    run(d([(0, 1000000)], 1))
    bad(d([(0, 1)] * 201), EV)
    bad(d([(0, 1)] * 10**5), EV)
    bad(d([]), EV)
    bad(d([(0, 1000001)]), "action out of range")
    bad(d([(-1, 5)]), "urge out of range")
    bad(d([(0, -1)]), "action out of range")
    bad(d([(1000001, 1000001)]), "urge out of range")
    bad(d([(5, 4)]), "action must not be before urge")
    bad(d(cd=0), "cooldown out of range")
    bad(d(cd=100001), "cooldown out of range")
    run(d(cd=100000))


@pytest.mark.parametrize("v", [True, False, 1.0, 1.5, None, "1", [1], {}])
def test_nonint(v):
    bad(d(cd=v), "cooldown must be an int")
    x = d()
    x["events"] = [[v, 5]]
    bad(x, "urge must be an int")
    x["events"] = [[0, v]]
    bad(x, "action must be an int")


@pytest.mark.parametrize("v", [True, False, 1, 1.5, None, "ab", {}, ("a",)])
def test_noncontainer(v):
    x = d()
    x["events"] = v
    bad(x, EV)
    x["events"] = [v]
    bad(x, "event must be an [urge, action] pair")
    for p in ([1], [1, 2, 3]):
        x["events"] = [p]
        bad(x, "event must be an [urge, action] pair")


@pytest.mark.parametrize("x", [None, 1, "a", [], True, [("events", 1)]])
def test_data_not_dict(x):
    bad(x, KEYS)


def test_keys_exact():
    for k in ("events", "cooldown"):
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
    a["events"][0]["wait"] = -1
    r = run(x)
    assert r["claims"]["health_claim"] is False and r["events"][0]["wait"] == 30 and m.CLAIMS["health_claim"] is False


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
            with pytest.raises(CooldownError) as e:
                run(_put(base, p, cls(_get(base, p))))
            assert "must be an int" in str(e.value) or "must be ints" in str(e.value)


def _get(x, path):
    for k in path:
        x = x[k]
    return x

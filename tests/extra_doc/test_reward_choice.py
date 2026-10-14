import copy
import random
from fractions import Fraction as F

import pytest

from sugarcode.extra_doc import reward_choice as m
from sugarcode.extra_doc.reward_choice import RewardError, reward_choice as run

KEYS = "data keys must be exactly delay, later, rate_den, rate_num, sooner"


def d(**kw):
    x = {"sooner": 100, "later": 150, "delay": 5, "rate_num": 1, "rate_den": 10}
    x.update(kw)
    return x


def bad(data, msg):
    with pytest.raises(RewardError) as e:
        run(data)
    assert str(e.value) == msg


def oracle(x):
    """Independent integer cross-multiplication: later*den vs sooner*(den + num*delay)."""
    lhs = x["later"] * x["rate_den"]
    rhs = x["sooner"] * (x["rate_den"] + x["rate_num"] * x["delay"])
    return "later" if lhs > rhs else "sooner" if lhs < rhs else "tie"


def check(x):
    o = run(x)
    assert o["choice"] == oracle(x)
    assert F(o["later_value_now"]) * (x["rate_den"] + x["rate_num"] * x["delay"]) == x["later"] * x["rate_den"]
    assert F(o["break_even_rate"]) * x["sooner"] * x["delay"] == x["later"] - x["sooner"]
    return o


def test_hand_worked():
    o = run(d())
    # rate 1/10 over 5 periods: 1 + 1/2 = 3/2 ; 150 / (3/2) = 100 -> tie ; break-even (50)/(500) = 1/10
    assert o["choice"] == "tie" and o["later_value_now"] == "100" and o["break_even_rate"] == "1/10"
    assert run(d(rate_num=0))["choice"] == "later" and run(d(rate_num=0))["later_value_now"] == "150"
    o = run(d(rate_num=2))
    assert o["choice"] == "sooner" and o["later_value_now"] == "75"
    assert o["status"] == "completed"
    assert o["claims"] == {"real_rate": False, "models_people": False, "comparable_rewards": False, "real_world": False}
    assert len(o["not_claimed"]) == 4
    assert run(d(sooner=3, later=4, delay=1, rate_num=1, rate_den=7))["later_value_now"] == "7/2"
    assert run(d(sooner=3, later=4, delay=1, rate_num=1, rate_den=7))["choice"] == "later"


def test_one_unit_either_side_of_tie():
    assert check(d(later=151))["choice"] == "later"
    assert check(d(later=149))["choice"] == "sooner"
    assert check(d(sooner=99))["choice"] == "later"
    assert check(d(sooner=101))["choice"] == "sooner"
    assert check(d(delay=4))["choice"] == "later"
    assert check(d(delay=6))["choice"] == "sooner"


def test_random():
    rng = random.Random(801)
    for _ in range(500):
        s = rng.randint(1, 50)
        check({"sooner": s, "later": s + rng.randint(1, 50), "delay": rng.randint(1, 20),
               "rate_num": rng.randint(0, 100), "rate_den": rng.randint(1, 100)})


RANGES = {"sooner": (1, 1000000), "delay": (1, 3650), "rate_num": (0, 100), "rate_den": (1, 100)}


def test_ranges():
    for k, (lo, hi) in RANGES.items():
        if k != "sooner":
            run(d(**{k: lo}))
            run(d(**{k: hi}))
        bad(d(**{k: lo - 1}), f"{k} out of range")
        bad(d(**{k: hi + 1}), f"{k} out of range")
    run(d(sooner=1))
    run(d(sooner=999999, later=1000000))
    bad(d(sooner=1000000, later=1000000), "later must be greater than sooner")
    bad(d(later=1000001), "later out of range")
    bad(d(later=0), "later out of range")
    bad(d(later=1), "later must be greater than sooner")
    bad(d(later=100), "later must be greater than sooner")
    bad(d(later=99), "later must be greater than sooner")
    run(d(later=101))


@pytest.mark.parametrize("k", ["sooner", "later", "delay", "rate_num", "rate_den"])
@pytest.mark.parametrize("v", [True, False, 1.0, 1.5, None, "1", [1], {}])
def test_nonint(k, v):
    bad(d(**{k: v}), f"{k} must be an int")


@pytest.mark.parametrize("x", [None, 1, "a", [], True, [("sooner", 1)]])
def test_data_not_dict(x):
    bad(x, KEYS)


def test_keys_exact():
    for k in d():
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
    a["not_claimed"].append("x")
    r = run(x)
    assert r["claims"]["real_world"] is False and len(r["not_claimed"]) == 4 and m.CLAIMS["real_world"] is False


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
            with pytest.raises(RewardError) as e:
                run(_put(base, p, cls(_get(base, p))))
            assert "must be an int" in str(e.value) or "must be ints" in str(e.value)


def _get(x, path):
    for k in path:
        x = x[k]
    return x

import copy
import random
from fractions import Fraction as F

import pytest

from sugarcode.extra_doc import physics_engine as m
from sugarcode.extra_doc.physics_engine import PhysicsError, physics_engine as run

ORDER = "gravity, height, restitution_den, restitution_num, steps, steps_per_unit, velocity"
KEYS = "data keys must be exactly " + ORDER


def d(**kw):
    x = {"height": 10, "velocity": 0, "gravity": 10, "steps_per_unit": 10, "steps": 5,
         "restitution_num": 1, "restitution_den": 2}
    x.update(kw)
    return x


def bad(data, msg):
    with pytest.raises(PhysicsError) as e:
        run(data)
    assert str(e.value) == msg


def oracle(x):
    """Independent: closed form per flight segment, y_k = y0 + k*v0*dt - g*dt^2*k(k+1)/2,
    v_k = v0 - k*g*dt; the first k with y_k < 0 ends the segment and restarts it."""
    dt = F(1, x["steps_per_unit"])
    g, e = x["gravity"], F(x["restitution_num"], x["restitution_den"])
    y0, v0 = F(x["height"]), F(x["velocity"])
    done, bounces, first, top = 0, 0, None, y0
    while done < x["steps"]:
        left = x["steps"] - done
        hit = None
        for k in range(1, left + 1):
            yk = y0 + k * v0 * dt - g * dt * dt * F(k * (k + 1), 2)
            if yk >= 0:
                top = max(top, yk)
            if yk < 0:
                hit = k
                break
        if hit is None:
            k = left
            return (y0 + k * v0 * dt - g * dt * dt * F(k * (k + 1), 2), v0 - k * g * dt, bounces, first, top)
        vk = v0 - hit * g * dt
        done += hit
        bounces += 1
        first = first if first is not None else done
        y0, v0 = F(0), -vk * e
        top = max(top, y0)
    return (y0, v0, bounces, first, top)


def check(x):
    o = run(x)
    y, v, b, f, t = oracle(x)
    assert (F(o["final_height"]), F(o["final_velocity"]), o["bounces"], o["first_bounce_step"], F(o["max_height"])) == (y, v, b, f, t)
    return o


def test_hand_worked_no_bounce():
    # dt=1/10, g=10: v after step1 = -1, y = 10 - 0.1 = 9.9; step2 v=-2, y=9.7
    o = run(d(steps=2))
    assert (o["final_height"], o["final_velocity"], o["bounces"], o["first_bounce_step"], o["max_height"]) == ("97/10", "-2", 0, None, "10")
    assert o["status"] == "completed"
    assert o["claims"] == {"matches_real_physics": False, "step_adequate": False, "real_object": False, "real_world": False}
    assert len(o["not_claimed"]) == 4
    check(d(steps=2))


def test_hand_worked_bounce():
    # height 0, v0 0: step1 v=-1, y=-1/10 <0 -> y=0, v=+1/2, bounce at step 1
    o = run(d(height=0, steps=1))
    assert (o["final_height"], o["final_velocity"], o["bounces"], o["first_bounce_step"]) == ("0", "1/2", 1, 1)
    # step 2: v=-1/2, y=-1/20 <0 -> bounce again, v=1/4
    o = run(d(height=0, steps=2))
    assert (o["final_velocity"], o["bounces"]) == ("1/4", 2)


def test_upward_launch_max_height():
    o = run(d(height=0, velocity=10, steps=3, steps_per_unit=1, gravity=1))
    # v: 9, 8, 7 ; y: 9, 17, 24
    assert (o["final_height"], o["final_velocity"], o["max_height"], o["bounces"]) == ("24", "7", "24", 0)
    check(d(height=0, velocity=10, steps=3, steps_per_unit=1, gravity=1))


def test_zero_restitution_stays_on_floor():
    o = check(d(height=1, restitution_num=0, steps=40))
    assert o["bounces"] > 0
    o2 = run(d(height=0, restitution_num=0, steps=3))
    assert o2["final_velocity"] == "0" or o2["final_velocity"] == "0/1"


def test_full_restitution_and_boundaries():
    check(d(restitution_num=10, restitution_den=10, steps=500))
    check(d(height=1000, velocity=100, gravity=100, steps_per_unit=100, steps=500, restitution_num=10, restitution_den=10))
    check(d(height=0, velocity=-100, gravity=1, steps_per_unit=1, steps=500, restitution_num=0, restitution_den=1))


def test_random_against_oracle():
    rng = random.Random(77)
    for _ in range(300):
        den = rng.randint(1, 10)
        check(d(height=rng.randint(0, 30), velocity=rng.randint(-20, 20), gravity=rng.randint(1, 20),
                steps_per_unit=rng.randint(1, 12), steps=rng.randint(1, 60),
                restitution_den=den, restitution_num=rng.randint(0, den)))


RANGES = {"height": (0, 1000), "velocity": (-100, 100), "gravity": (1, 100), "steps_per_unit": (1, 100),
          "steps": (1, 500), "restitution_den": (1, 10)}


def test_ranges():
    for k, (lo, hi) in RANGES.items():
        kw = {k: lo}
        run(d(**kw))
        kw = {k: hi}
        run(d(**kw))
        bad(d(**{k: lo - 1}), f"{k} out of range")
        bad(d(**{k: hi + 1}), f"{k} out of range")
    bad(d(restitution_num=-1), "restitution_num out of range")
    bad(d(restitution_num=3), "restitution_num out of range")
    run(d(restitution_num=2))
    bad(d(restitution_den=1, restitution_num=2), "restitution_num out of range")


@pytest.mark.parametrize("k", list(RANGES) + ["restitution_num"])
@pytest.mark.parametrize("v", [True, False, 1.0, 1.5, None, "1", [1], {}])
def test_nonint(k, v):
    bad(d(**{k: v}), f"{k} must be an int")


@pytest.mark.parametrize("x", [None, 1, "a", [], True, [("height", 1)]])
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
            with pytest.raises(PhysicsError) as e:
                run(_put(base, p, cls(_get(base, p))))
            assert "must be an int" in str(e.value) or "must be ints" in str(e.value)


def _get(x, path):
    for k in path:
        x = x[k]
    return x

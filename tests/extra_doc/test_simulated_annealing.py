import copy
import random
from fractions import Fraction

import pytest

from sugarcode.extra_doc import simulated_annealing as m
from sugarcode.extra_doc.simulated_annealing import AnnealingError, simulated_annealing as run

KEYS = "data keys must be exactly landscape, start, steps, t0, cool_num, cool_den, seed"
LITERAL_NOT_CLAIMED = [
    "the run finds the global minimum",
    "the acceptance rule matches the Metropolis rule",
    "the generator is statistically strong",
    "real-world outcome",
]
BASE = {"landscape": [3, 1, 2, 0], "start": 1, "steps": 6, "t0": 2, "cool_num": 1, "cool_den": 2, "seed": 1}


def d(**kw):
    out = copy.deepcopy(BASE)
    out.update(kw)
    return out


def bad(data, msg):
    with pytest.raises(AnnealingError) as e:
        run(data)
    assert str(e.value) == msg


def stream(seed):
    x = seed
    while True:
        x = (1103515245 * x + 12345) % 2147483648
        yield x // 65536


def reference(cfg):
    g = stream(cfg["seed"])
    L = cfg["landscape"]
    pos = cfg["start"]
    T = Fraction(cfg["t0"])
    r = Fraction(cfg["cool_num"], cfg["cool_den"])
    best = (L[pos], pos)
    path = [pos]
    counts = {"down": 0, "ut": 0, "ur": 0, "off": 0}
    for _ in range(cfg["steps"]):
        step = 1 if next(g) % 2 == 1 else -1
        q = pos + step
        if q in range(len(L)):
            dl = L[q] - L[pos]
            if dl <= 0:
                pos = q
                counts["down"] += 1
            else:
                u = next(g) % 32768
                if Fraction(u, 32768) < T / (T + dl):
                    pos = q
                    counts["ut"] += 1
                else:
                    counts["ur"] += 1
            if L[pos] < best[0]:
                best = (L[pos], pos)
        else:
            counts["off"] += 1
        path.append(pos)
        T *= r
    return best, pos, path, counts


def test_generator_start_pinned_and_hand_trace():
    g = stream(1)
    assert [next(g) for _ in range(6)] == [16838, 5758, 10113, 17515, 31051, 5627]
    out = run(d())
    # step 0 left (even), uphill 3-1=2 at T=2: 5758*4 = 23032 < 65536 accepted; step 1 right downhill;
    # steps 2-5 are uphill proposals refused at T = 1/2, 1/4, 1/8, 1/16 ... (checked draw by draw)
    assert out["path"] == [1, 0, 1, 1, 1, 1, 1]
    assert out["downhill_or_level_moves"] == 1 and out["uphill_accepted"] == 1
    assert out["uphill_refused"] == 4 and out["off_end_rejected"] == 0
    assert out["best_cost"] == 1 and out["best_position"] == 1 and out["final_position"] == 1
    assert out["landscape_minimum"] == 0 and out["best_is_minimum"] is False


def test_matches_second_implementation_on_random_configs():
    rng = random.Random(21)
    for _ in range(80):
        n = rng.randint(3, 15)
        cfg = {"landscape": [rng.randint(-20, 20) for _ in range(n)], "start": rng.randrange(n),
               "steps": rng.randint(1, 60), "t0": rng.randint(1, 50), "cool_den": rng.randint(1, 20),
               "seed": rng.randint(0, 2 ** 31 - 1)}
        cfg["cool_num"] = rng.randint(1, cfg["cool_den"])
        out = run(cfg)
        best, pos, path, c = reference(cfg)
        assert (out["best_cost"], out["best_position"]) == best, cfg
        assert out["final_position"] == pos and out["path"] == path
        assert (out["downhill_or_level_moves"], out["uphill_accepted"], out["uphill_refused"], out["off_end_rejected"]) \
            == (c["down"], c["ut"], c["ur"], c["off"])
        assert sum(c.values()) == cfg["steps"]
        assert out["landscape_minimum"] == min(cfg["landscape"])


def test_off_end_moves_are_rejected_and_do_not_consume_an_acceptance_draw():
    # seed 1 draws an even number first: a move left from position 0 is off the end
    out = run(d(start=0, steps=1))
    assert out["off_end_rejected"] == 1 and out["path"] == [0, 0]
    # the draw after it must be the next stream value: the second step's direction is 5758 -> left again
    out = run(d(start=0, steps=2))
    assert out["off_end_rejected"] == 2
    out = run(d(landscape=[0, 1, 2], start=2, steps=3, seed=2))
    best, pos, path, c = reference(d(landscape=[0, 1, 2], start=2, steps=3, seed=2))
    assert out["path"] == path and out["off_end_rejected"] == c["off"]


def test_temperature_schedule_and_acceptance_threshold():
    # delta 1 uphill at T: accepted iff u * (T + 1) < T * 32768. With a huge ratio-1 temperature almost every
    # uphill move is taken; with t0 = 1 and strong cooling almost none are.
    land = [0, 1, 0, 1, 0, 1, 0, 1, 0, 1]
    hot = run(d(landscape=land, start=0, steps=100, t0=1000, cool_num=1, cool_den=1, seed=3))
    cold = run(d(landscape=land, start=0, steps=100, t0=1, cool_num=1, cool_den=100, seed=3))
    assert hot["uphill_accepted"] > cold["uphill_accepted"]
    assert hot["uphill_accepted"] + hot["uphill_refused"] > 0 and cold["uphill_refused"] > 0
    # exact threshold: at T = 1, delta = 1 the probability is 1/2: u = 16383 accepted, u = 16384 refused
    assert 16383 * (1 + 1) < 1 * 32768 and not 16384 * (1 + 1) < 1 * 32768


def test_properties_best_path_and_counts():
    cfg = d(landscape=[5, 3, 4, 2, 6, 1, 3], start=0, steps=100, t0=10, cool_num=9, cool_den=10, seed=99)
    out = run(cfg)
    L = cfg["landscape"]
    assert len(out["path"]) == 101 and out["path"][0] == 0 and out["path"][-1] == out["final_position"]
    assert all(abs(a - b) <= 1 for a, b in zip(out["path"], out["path"][1:]))
    assert out["best_cost"] == min(L[p] for p in out["path"]) and L[out["best_position"]] == out["best_cost"]
    assert out["downhill_or_level_moves"] + out["uphill_accepted"] + out["uphill_refused"] + out["off_end_rejected"] == 100
    assert out["best_is_minimum"] == (out["best_cost"] == 1)
    assert run(cfg) == out


def test_claims_and_input_not_mutated():
    data = d()
    before = copy.deepcopy(data)
    out = run(data)
    assert data == before
    assert out["claims"] == {"finds_minimum": False, "metropolis": False, "generator_strong": False, "real_world": False}
    out["claims"]["real_world"] = True
    out["not_claimed"].append("x")
    out["path"][0] = 99
    again = run(data)
    assert again["claims"]["real_world"] is False and again["not_claimed"] == LITERAL_NOT_CLAIMED
    assert again["path"][0] == 1
    assert tuple(again["not_claimed"]) == m.NOT_CLAIMED


def test_constants():
    assert (m.MIN_N, m.MAX_N, m.MAX_COST, m.MAX_STEPS, m.MAX_T0, m.MAX_DEN, m.MAX_SEED) == \
        (3, 40, 1000, 100, 1000, 100, 2147483647)


def test_refusals_and_caps():
    for x in (None, [], {"landscape": []}, dict(d(), extra=1)):
        bad(x, KEYS)
    bad(d(landscape="abc"), "landscape must be a list")
    bad(d(landscape=[1, 2]), "landscape length out of range")
    bad(d(landscape=[1] * 41, start=0), "landscape length out of range")
    run(d(landscape=[1] * 40, start=39))
    for name in ("start", "steps", "t0", "cool_num", "cool_den", "seed"):
        for v in (True, 1.0, "1", None):
            bad(d(**{name: v}), f"{name} must be an int")
    bad(d(start=-1), "start out of range")
    bad(d(start=4), "start out of range")
    run(d(start=0))
    run(d(start=3))
    bad(d(steps=0), "steps out of range")
    bad(d(steps=101), "steps out of range")
    run(d(steps=100))
    bad(d(t0=0), "t0 out of range")
    bad(d(t0=1001), "t0 out of range")
    run(d(t0=1000))
    bad(d(cool_den=0), "cool_den out of range")
    bad(d(cool_den=101), "cool_den out of range")
    bad(d(cool_num=0), "cool_num out of range")
    bad(d(cool_num=3), "cool_num out of range")
    run(d(cool_num=2, cool_den=2))
    run(d(cool_num=100, cool_den=100))
    bad(d(seed=-1), "seed out of range")
    bad(d(seed=2147483648), "seed out of range")
    run(d(seed=2147483647))
    run(d(seed=0))
    for v in (True, 1.0, "1", None):
        bad(d(landscape=[v, 1, 2, 0]), "cost must be an int")
    bad(d(landscape=[1001, 1, 2, 0]), "cost out of range")
    bad(d(landscape=[-1001, 1, 2, 0]), "cost out of range")
    run(d(landscape=[1000, -1000, 2, 0]))


def one_step(seed, t0):
    return run(d(landscape=[0, 1, 2], start=0, steps=1, t0=t0, cool_num=1, cool_den=1, seed=seed))


def test_acceptance_boundaries_with_found_seeds():
    # seed 8250: first draw odd (move right, uphill by 1), acceptance draw u = 16384; T = 1 gives u * 2 == 32768,
    # an exact tie, which is refused because the rule is strict
    out = one_step(8250, 1)
    assert out["path"] == [0, 0] and out["uphill_refused"] == 1 and out["uphill_accepted"] == 0
    # seed 5287: u = 32767, the largest draw; refused even at T = 1000 (32767 * 1001 > 1000 * 32768)
    out = one_step(5287, 1000)
    assert out["path"] == [0, 0] and out["uphill_refused"] == 1
    # seed 36277: u = 32735; at T = 1000, 32735 * 1001 = 32767735 < 32768000 so it is accepted
    out = one_step(36277, 1000)
    assert out["path"] == [0, 1] and out["uphill_accepted"] == 1
    # the same draw at T = 1 is refused
    assert one_step(36277, 1)["uphill_refused"] == 1


def test_long_run_pins_modulus_2_pow_31():
    out = run(d(landscape=[5, 3, 8, 1, 9, 2, 7, 4, 6, 0], start=4, steps=100, t0=50, cool_num=9, cool_den=10,
                seed=2147483647))
    assert out["path"][:20] == [4, 5, 6, 5, 6, 5, 6, 5, 6, 7, 6, 5, 5, 6, 7, 6, 5, 5, 4, 5]
    assert out["path"][28:40] == [7, 7, 7, 6, 5, 5, 5, 4, 5, 5, 5, 5]
    assert out["path"][70:80] == [5, 5, 5, 5, 5, 4, 5, 5, 5, 5]
